"""FastAPI application entry point for Accounts Service."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from accounts import router as accounts_router
# from accounts import transaction_router
from config import get_settings
from database import create_tables
from events.auth_handlers import (
    UserDeletedHandler,
    UserLoggedInHandler,
    UserRegisteredHandler,
)
from schemas import HealthResponse
from shared.events.infrastructure.sqs_setup import subscribe_queue_to_topic
from shared.events.sqs_subscriber import SQSSubscriber
from shared.logging_config import setup_logging

# Configure logging before creating logger
settings = get_settings()
setup_logging(debug=settings.debug)

logger = logging.getLogger(__name__)


async def setup_auth_event_subscription(app: FastAPI) -> SQSSubscriber:
    """Set up subscription to auth service events via SNS → SQS.

    Creates an SQS queue, subscribes it to the auth SNS topic,
    and starts polling for events.

    Args:
        app: FastAPI application instance

    Returns:
        The configured and started SQS subscriber
    """
    # Subscribe accounts queue to auth SNS topic
    queue_url, subscription_arn = await subscribe_queue_to_topic(
        queue_name=settings.aws_accounts_auth_events_queue,
        topic_arn=settings.auth_topic_arn,
        region_name=settings.aws_region,
        endpoint_url=settings.aws_endpoint_url,
    )

    logger.info(
        f"Subscribed to auth events: queue={queue_url}, "
        f"subscription={subscription_arn}"
    )

    # Create and configure the SQS subscriber
    subscriber = SQSSubscriber(
        queue_url=queue_url,
        region_name=settings.aws_region,
        endpoint_url=settings.aws_endpoint_url,
        max_messages=10,
        wait_time_seconds=20,
        visibility_timeout=60,
    )

    # Register event handlers
    subscriber.register_handler(UserRegisteredHandler())
    subscriber.register_handler(UserDeletedHandler())
    subscriber.register_handler(UserLoggedInHandler())

    # Start consuming events
    await subscriber.connect()
    await subscriber.start()

    return subscriber


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    create_tables()

    # Subscribe to auth service events (SNS → SQS fan-out)
    auth_subscriber = await setup_auth_event_subscription(app)
    app.state.auth_subscriber = auth_subscriber

    logger.info("Accounts service started - listening for auth events")

    yield

    # Shutdown - stop the subscriber gracefully
    if hasattr(app.state, "auth_subscriber"):
        await app.state.auth_subscriber.stop()
        await app.state.auth_subscriber.disconnect()
        logger.info("Auth event subscriber stopped")


app = FastAPI(
    title=settings.app_name,
    description="Accounts service for FlowForward Finance platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(accounts_router)
# app.include_router(transaction_router)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns service health status.
    """
    return HealthResponse(
        status="healthy",
        service="accounts-service",
        version="0.1.0",
    )


@app.get("/", tags=["Root"])
def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "service": "FlowForward Accounts Service",
        "version": "0.1.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.debug,
    )
