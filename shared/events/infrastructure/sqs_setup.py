
import logging
from typing import Any

import aioboto3
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)

class InfrastructureError(Exception):
    """Exception raised when infrastructure setup fails."""
    pass

async def setup_sqs_queue(
    queue_name: str,
    region_name: str = "us-east-1",
    account_id: str = "000000000000",
    endpoint_url: str | None = None,
    **boto_kwargs: Any
) -> None:
    """Setup SQS infrastructure."""
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
        if e.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
            attributes = {
                "MessageRetentionPeriod": "345600",
                "VisibilityTimeout": "60"
                # TODO: setup DLQ
                # "RedrivePolicy": '{"deadLetterTargetArn": "$DLQ_ARN", "maxReceiveCount": "3"}',
            }
            response = await client.create_queue(QueueName=queue_name, Attributes=attributes)
            queue_url = response["QueueUrl"]
            logger.info(f"Created SQS queue: {queue_url}")
            return queue_url
        raise
    except Exception as e:
        raise InfrastructureError(f"Failed to ensure SQS queue {queue_name}: {e}") from e