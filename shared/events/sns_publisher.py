"""SNS Event publisher implementation.

Provides an SNS-based publisher for publishing domain events to SNS topics.
"""

import json
import logging
from typing import Any

import aioboto3

from shared.events.base import DomainEvent
from shared.events.publisher import EventPublisher, PublishError

logger = logging.getLogger(__name__)


class SNSPublisher(EventPublisher):
    """SNS-based event publisher.

    Publishes domain events to an SNS topic for fan-out to subscribers.

    Example:
        >>> publisher = SNSPublisher(
        ...     topic_arn="arn:aws:sns:us-east-1:123456789:auth-events",
        ...     region_name="us-east-1",
        ... )
        >>> await publisher.connect()
        >>> await publisher.publish(event)
    """

    def __init__(
        self,
        topic_arn: str,
        region_name: str = "us-east-1",
        endpoint_url: str | None = None,
        **boto_kwargs: Any,
    ) -> None:
        """Initialize the SNS publisher.

        Args:
            topic_arn: ARN of the SNS topic to publish to
            region_name: AWS region
            endpoint_url: Optional endpoint URL (for LocalStack)
            **boto_kwargs: Additional boto3 client kwargs
        """
        self._topic_arn = topic_arn
        self._region_name = region_name
        self._endpoint_url = endpoint_url
        self._boto_kwargs = boto_kwargs
        self._session: aioboto3.Session | None = None
        self._connected = False

    @property
    def topic_arn(self) -> str:
        """Get the topic ARN."""
        return self._topic_arn

    async def connect(self) -> None:
        """Initialize the boto3 session."""
        self._session = aioboto3.Session()
        self._connected = True
        logger.info(f"SNSPublisher connected to topic: {self._topic_arn}")

    async def disconnect(self) -> None:
        """Clean up resources."""
        self._session = None
        self._connected = False
        logger.info("SNSPublisher disconnected")

    async def publish(
        self,
        event: DomainEvent[Any],
        topic: str | None = None,
    ) -> None:
        """Publish a domain event to SNS.

        Args:
            event: The domain event to publish
            topic: Optional topic ARN override

        Raises:
            PublishError: If publishing fails
        """
        if not self._session:
            raise PublishError("Publisher not connected", event)

        target_topic = topic or self._topic_arn
        message = json.dumps(event.to_dict())

        try:
            async with self._session.client(
                "sns",
                region_name=self._region_name,
                endpoint_url=self._endpoint_url,
                **self._boto_kwargs,
            ) as sns_client:
                response = await sns_client.publish(
                    TopicArn=target_topic,
                    Message=message,
                    MessageAttributes={
                        "event_type": {
                            "DataType": "String",
                            "StringValue": event.event_type,
                        },
                        "event_id": {
                            "DataType": "String",
                            "StringValue": event.metadata.event_id,
                        },
                        "source": {
                            "DataType": "String",
                            "StringValue": event.metadata.source,
                        },
                    },
                )

                logger.debug(
                    f"Published event {event.event_type} "
                    f"(id={event.metadata.event_id}) "
                    f"to {target_topic}, "
                    f"MessageId={response['MessageId']}"
                )

        except Exception as e:
            logger.error(f"Failed to publish event {event.event_type}: {e}")
            raise PublishError(
                f"Failed to publish event to SNS: {e}",
                event,
            ) from e

    async def publish_batch(
        self,
        events: list[DomainEvent[Any]],
        topic: str | None = None,
    ) -> None:
        """Publish multiple events.

        Note: SNS doesn't support batch publishing natively,
        so this publishes events sequentially.

        Args:
            events: List of domain events to publish
            topic: Optional topic ARN override

        Raises:
            PublishError: If any publish fails
        """
        for event in events:
            await self.publish(event, topic)

