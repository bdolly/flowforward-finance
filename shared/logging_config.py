"""Shared logging configuration for all services.

Provides a consistent logging setup across all microservices.
"""

import logging
import sys
from typing import Optional


def setup_logging(
    debug: bool = False,
    level: Optional[int] = None,
    format_string: Optional[str] = None,
    date_format: Optional[str] = None,
) -> None:
    """Configure logging for the application.

    Sets up logging with appropriate handlers and formatting for containerized
    environments. Logs are output to stdout for Docker container log capture.

    Args:
        debug: If True, sets log level to DEBUG, otherwise INFO
        level: Optional explicit log level (overrides debug parameter)
        format_string: Optional custom format string for log messages
        date_format: Optional custom date format string

    Example:
        >>> setup_logging(debug=True)
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("This will be logged")
    """
    log_level = level if level is not None else (logging.DEBUG if debug else logging.INFO)
    log_format = format_string or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_date_format = date_format or "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=log_date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
        force=True,  # Override any existing configuration
    )

