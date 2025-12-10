import logging
from typing import Any

import aioboto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class InfrastructureError(Exception):
    """Exception raised when infrastructure setup fails."""
    pass


async def setup_sns_topic(
    topic_name: str,
    region_name: str = "us-east-1",
    account_id: str = "000000000000",
    endpoint_url: str | None = None,
    **boto_kwargs: Any
) -> str:
    """Setup SNS infrastructure.

    Args:
        topic_name: The name of the SNS topic to create
        region_name: The AWS region to use
        account_id: The AWS account ID to use
        endpoint_url: The URL of the LocalStack endpoint
        **boto_kwargs: Additional keyword arguments to pass to the SNS client
    """
    session = aioboto3.Session()

    try:
        async with session.client(
            "sns",
            region_name=region_name,
            endpoint_url=endpoint_url,
            **boto_kwargs,
        ) as client:
            try:
                topic_arn_str = (
                    f"arn:aws:sns:{region_name}:{account_id}:{topic_name}"
                )
                response = await client.get_topic_attributes(
                    TopicArn=topic_arn_str
                )
                topic_arn = response["Attributes"]["TopicArn"]
                logger.info(f"SNS topic already exists: {topic_arn}")
                return topic_arn
            except ClientError as e:
                if e.response["Error"]["Code"] == "NotFound":
                    response = await client.create_topic(Name=topic_name)
                    topic_arn = response["TopicArn"]
                    logger.info(f"Created SNS topic: {topic_arn}")
                    return topic_arn
                raise
    except Exception as e:
        error_msg = f"Failed to ensure SNS topic {topic_name}: {e}"
        raise InfrastructureError(error_msg) from e
