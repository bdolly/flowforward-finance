"""SQS Event subscriber implementation.

Provides an SQS-based subscriber for consuming events from SNS via SQS queues
following the fan-out pattern.
"""

import asyncio
import json
import logging
from typing import Any

import aioboto3
from pydantic import BaseModel

from shared.events.base import DomainEvent, EventMetadata
from shared.events.subscriber import EventSubscriber

logger = logging.getLogger(__name__)


class SQSSubscriber(EventSubscriber):
    """SQS-based event subscriber for SNS → SQS fan-out pattern.

    Polls messages from an SQS queue that is subscribed to an SNS topic.
    Messages are automatically parsed from the SNS envelope format.

    Example:
        >>> subscriber = SQSSubscriber(
        ...     queue_url="https://sqs.us-east-1.amazonaws.com/123456789/my-queue",
        ...     region_name="us-east-1",
        ... )
        >>> subscriber.register_handler(UserRegisteredHandler())
        >>> await subscriber.start()
    """

    def __init__(
        self,
        queue_url: str,
        region_name: str = "us-east-1",
        endpoint_url: str | None = None,
        max_messages: int = 10,
        wait_time_seconds: int = 20,
        visibility_timeout: int = 60,
        poll_interval: float = 1.0,
        **boto_kwargs: Any,
    ) -> None:
        """Initialize the SQS subscriber.

        Args:
            queue_url: Full URL of the SQS queue to poll
            region_name: AWS region
            endpoint_url: Optional endpoint URL (for LocalStack)
            max_messages: Maximum messages to receive per poll (1-10)
            wait_time_seconds: Long polling wait time (0-20)
            visibility_timeout: Visibility timeout for received messages
            poll_interval: Interval between polls when queue is empty
            **boto_kwargs: Additional boto3 client kwargs
        """
        super().__init__()
        self._queue_url = queue_url
        self._region_name = region_name
        self._endpoint_url = endpoint_url
        self._max_messages = max_messages
        self._wait_time_seconds = wait_time_seconds
        self._visibility_timeout = visibility_timeout
        self._poll_interval = poll_interval
        self._boto_kwargs = boto_kwargs
        self._running = False
        self._consumer_task: asyncio.Task[None] | None = None
        self._session: aioboto3.Session | None = None

    async def connect(self) -> None:
        """Initialize the boto3 session."""
        self._session = aioboto3.Session()
        logger.info(f"SQSSubscriber connected to queue: {self._queue_url}")

    async def disconnect(self) -> None:
        """Clean up resources."""
        self._session = None
        logger.info("SQSSubscriber disconnected")

    async def start(self, topics: list[str] | None = None) -> None:
        """Start polling for messages.

        Args:
            topics: Ignored for SQS subscriber (queue is already subscribed)
        """
        if self._running:
            logger.warning("SQSSubscriber already running")
            return

        if not self._session:
            await self.connect()

        self._running = True
        self._consumer_task = asyncio.create_task(self._poll_messages())
        logger.info(f"SQSSubscriber started polling queue: {self._queue_url}")

    async def stop(self) -> None:
        """Stop polling for messages."""
        self._running = False
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
            self._consumer_task = None
        logger.info("SQSSubscriber stopped")

    async def _poll_messages(self) -> None:
        """Internal message polling loop."""
        while self._running:
            try:
                async with self._session.client(
                    "sqs",
                    region_name=self._region_name,
                    endpoint_url=self._endpoint_url,
                    **self._boto_kwargs,
                ) as sqs_client:
                    response = await sqs_client.receive_message(
                        QueueUrl=self._queue_url,
                        MaxNumberOfMessages=self._max_messages,
                        WaitTimeSeconds=self._wait_time_seconds,
                        VisibilityTimeout=self._visibility_timeout,
                        AttributeNames=["All"],
                        MessageAttributeNames=["All"],
                    )

                    messages = response.get("Messages", [])
                    
                    if not messages:
                        await asyncio.sleep(self._poll_interval)
                        continue

                    for message in messages:
                        try:
                            await self._process_message(message, sqs_client)
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            # Message will become visible again after timeout

            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Error polling SQS queue: {e}")
                await asyncio.sleep(self._poll_interval)

    async def _process_message(
        self,
        message: dict[str, Any],
        sqs_client: Any,
    ) -> None:
        """Process a single SQS message.

        Args:
            message: The SQS message dict
            sqs_client: The SQS client for deleting the message
        """
        receipt_handle = message["ReceiptHandle"]
        body = message["Body"]

        try:
            # Parse the message body
            body_data = json.loads(body)
            
            # Check if this is an SNS notification (has Message field)
            if "Message" in body_data:
                # Extract the actual event from SNS envelope
                event_data = json.loads(body_data["Message"])
            else:
                # Direct SQS message
                event_data = body_data

            # Reconstruct the domain event
            event = self._parse_event(event_data)
            
            if event:
                logger.debug(
                    f"Received event: {event.event_type} "
                    f"(id={event.metadata.event_id})"
                )
                await self.dispatch(event)

            # Delete the message after successful processing
            await sqs_client.delete_message(
                QueueUrl=self._queue_url,
                ReceiptHandle=receipt_handle,
            )
            logger.debug(f"Deleted message: {message.get('MessageId')}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message JSON: {e}")
            # Delete malformed messages to prevent poison pill
            await sqs_client.delete_message(
                QueueUrl=self._queue_url,
                ReceiptHandle=receipt_handle,
            )
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            raise

    def _parse_event(self, event_data: dict[str, Any]) -> DomainEvent[Any] | None:
        """Parse event data into a DomainEvent.

        Args:
            event_data: The raw event data dictionary

        Returns:
            The parsed DomainEvent or None if parsing fails
        """
        try:
            # Handle both nested and flat event structures
            if "event_type" not in event_data:
                logger.warning(f"Message missing event_type: {event_data}")
                return None

            return DomainEvent.model_validate(event_data)
        except Exception as e:
            logger.error(f"Failed to parse event: {e}")
            return None

