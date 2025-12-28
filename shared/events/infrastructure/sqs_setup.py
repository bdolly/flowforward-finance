"""SQS infrastructure setup utilities."""

import json
import logging
from typing import Any

import aioboto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class InfrastructureError(Exception):
    """Exception raised when infrastructure setup fails."""

    pass


# TODO: eventually move this to terraform as it doesn't need to be done at runtime
async def setup_sqs_queue(
    queue_name: str,
    region_name: str = "us-east-1",
    account_id: str = "000000000000",
    endpoint_url: str | None = None,
    **boto_kwargs: Any
) -> str:
    """Setup SQS infrastructure.

    Args:
        queue_name: Name of the SQS queue
        region_name: AWS region
        account_id: AWS account ID
        endpoint_url: Optional LocalStack endpoint URL
        **boto_kwargs: Additional boto3 client kwargs

    Returns:
        str: The queue URL
    """
    session = aioboto3.Session()

    try:
        async with session.client(
            "sqs",
            region_name=region_name,
            endpoint_url=endpoint_url,
            **boto_kwargs,
        ) as client:
            response = await client.get_queue_url(QueueName=queue_name)
            queue_url = response["QueueUrl"]
            logger.info(f"SQS queue already exists: {queue_url}")
            return queue_url
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AWS.SimpleQueueService.NonExistentQueue":
            async with session.client(
                "sqs",
                region_name=region_name,
                endpoint_url=endpoint_url,
                **boto_kwargs,
            ) as client:
                attributes = {
                    "MessageRetentionPeriod": "345600",
                    "VisibilityTimeout": "60"
                }
                response = await client.create_queue(
                    QueueName=queue_name,
                    Attributes=attributes,
                )
                queue_url = response["QueueUrl"]
                logger.info(f"Created SQS queue: {queue_url}")
                return queue_url
        raise
    except Exception as e:
        msg = f"Failed to ensure SQS queue {queue_name}: {e}"
        raise InfrastructureError(msg) from e


# TODO: eventually move this to terraform as it doesn't need to be done at runtime
async def subscribe_queue_to_topic(
    queue_name: str,
    topic_arn: str,
    region_name: str = "us-east-1",
    endpoint_url: str | None = None,
    **boto_kwargs: Any,
) -> tuple[str, str]:
    """Subscribe an SQS queue to an SNS topic for fan-out pattern.

    Args:
        queue_name: Name of the SQS queue to subscribe
        topic_arn: ARN of the SNS topic
        region_name: AWS region
        endpoint_url: LocalStack endpoint URL
        **boto_kwargs: Additional boto3 client kwargs

    Returns:
        tuple[str, str]: (queue_url, subscription_arn)

    Raises:
        InfrastructureError: If subscription fails
    """
    session = aioboto3.Session()

    try:
        # Ensure queue exists first
        queue_url = await setup_sqs_queue(
            queue_name,
            region_name=region_name,
            endpoint_url=endpoint_url,
            **boto_kwargs,
        )

        async with session.client(
            "sqs",
            region_name=region_name,
            endpoint_url=endpoint_url,
            **boto_kwargs,
        ) as sqs_client:
            # Get queue ARN
            queue_attrs = await sqs_client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=["QueueArn"],
            )
            queue_arn = queue_attrs["Attributes"]["QueueArn"]

            async with session.client(
                "sns",
                region_name=region_name,
                endpoint_url=endpoint_url,
                **boto_kwargs,
            ) as sns_client:
                # Check if subscription already exists
                subs_resp = await sns_client.list_subscriptions_by_topic(
                    TopicArn=topic_arn
                )
                for sub in subs_resp.get("Subscriptions", []):
                    if sub["Endpoint"] == queue_arn:
                        logger.info(
                            f"Queue {queue_name} already subscribed "
                            f"to topic {topic_arn}"
                        )
                        return queue_url, sub["SubscriptionArn"]

                # Create subscription
                response = await sns_client.subscribe(
                    TopicArn=topic_arn,
                    Protocol="sqs",
                    Endpoint=queue_arn,
                    Attributes={
                        "RawMessageDelivery": "false",
                    },
                )
                subscription_arn = response["SubscriptionArn"]

            # Set queue policy to allow SNS to send messages
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "AllowSNSPublish",
                        "Effect": "Allow",
                        "Principal": {"Service": "sns.amazonaws.com"},
                        "Action": "sqs:SendMessage",
                        "Resource": queue_arn,
                        "Condition": {
                            "ArnEquals": {
                                "aws:SourceArn": topic_arn,
                            },
                        },
                    },
                ],
            }

            await sqs_client.set_queue_attributes(
                QueueUrl=queue_url,
                Attributes={"Policy": json.dumps(policy)},
            )

            logger.info(
                f"Subscribed queue {queue_name} to topic {topic_arn}"
            )
            return queue_url, subscription_arn

    except InfrastructureError:
        raise
    except Exception as e:
        raise InfrastructureError(
            f"Failed to subscribe queue {queue_name} to topic {topic_arn}: {e}"
        ) from e
