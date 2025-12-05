"""
Logging configuration using Loguru
"""
import sys
from loguru import logger
from pathlib import Path

# Create logs directory
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Remove default handler
logger.remove()

# Add console handler with custom format
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
    level="INFO",
    colorize=True
)

# Add file handler for all logs
logger.add(
    LOGS_DIR / "app_{time:YYYY-MM-DD}.log",
    rotation="00:00",  # Rotate at midnight
    retention="30 days",  # Keep logs for 30 days
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} | {message}",
    level="DEBUG"
)

# Add file handler for errors only
logger.add(
    LOGS_DIR / "errors_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="90 days",  # Keep error logs longer
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    level="ERROR"
)

def get_logger(name: str):
    """Get a logger instance with the specified name"""
    return logger.bind(name=name)


# Export logger
__all__ = ["logger", "get_logger"]
