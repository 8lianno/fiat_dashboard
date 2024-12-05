from pathlib import Path
import sys
from loguru import logger

def setup_logging():
    """Configure logging for the application"""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Remove default logger
    logger.remove()
    
    # Add file logger with rotation
    logger.add(
        "logs/finest_{time}.log",
        rotation="500 MB",
        retention="30 days",
        compression="zip",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        backtrace=True,
        diagnose=True
    )
    
    # Add stderr logger for warnings and errors
    logger.add(
        sys.stderr,
        level="WARNING",
        format="<red>{time:HH:mm:ss}</red> | <level>{level}</level> | <cyan>{message}</cyan>",
        colorize=True
    )
    
    # Add development logger for debugging
    if Path(".env").exists() and "DEV" in Path(".env").read_text():
        logger.add(
            "logs/debug_{time}.log",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            rotation="100 MB",
            retention="2 days"
        )
    
    logger.info("Logging configured successfully")
