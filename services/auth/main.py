"""FastAPI application entry point for Auth Service."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import router as auth_router
from config import get_settings
from database import create_tables
from events.publisher import AuthEventPublisher
from schemas import HealthResponse
from shared.events.infrastructure.sns_setup import setup_sns_topic
from shared.events.infrastructure.sqs_setup import setup_sqs_queue
from shared.events.sns_publisher import SNSPublisher
from shared.logging_config import setup_logging

# Configure logging before creating logger
settings = get_settings()
setup_logging(debug=settings.debug)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    create_tables()

    # Set up auth service event topic
    topic_arn = await setup_sns_topic(
        topic_name=settings.aws_auth_sns_topic_name,
        region_name=settings.aws_region,
        endpoint_url=settings.aws_endpoint_url,
    )
    app.state.auth_topic_arn = topic_arn

    # Set up SNS publisher for auth events
    sns_publisher = SNSPublisher(
        topic_arn=topic_arn,
        region_name=settings.aws_region,
        endpoint_url=settings.aws_endpoint_url,
    )
    await sns_publisher.connect()
    app.state.sns_publisher = sns_publisher

    # Create the typed auth event publisher facade
    app.state.event_publisher = AuthEventPublisher(sns_publisher)

    logger.info(f"Auth event publisher connected to topic: {topic_arn}")

    # Set up SQS queue (if needed for consuming events)
    sqs_queue_url = await setup_sqs_queue(
        queue_name=settings.aws_auth_sqs,
        region_name=settings.aws_region,
        endpoint_url=settings.aws_endpoint_url,
    )
    app.state.auth_sqs_queue_url = sqs_queue_url

    yield

    # Shutdown - disconnect publisher
    if hasattr(app.state, "sns_publisher"):
        await app.state.sns_publisher.disconnect()
        logger.info("Auth event publisher disconnected")


app = FastAPI(
    title=settings.app_name,
    description="Authentication service for FlowForward Finance platform",
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
app.include_router(auth_router)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns service health status.
    """
    return HealthResponse(
        status="healthy",
        service="auth-service",
        version="0.1.0",
    )


@app.get("/", tags=["Root"])
def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "service": "FlowForward Auth Service",
        "version": "0.1.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )


