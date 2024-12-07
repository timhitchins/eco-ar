
from datetime import datetime
import os
from logging.handlers import RotatingFileHandler
import logging


def setup_logging(log_level=logging.INFO) -> logging.Logger:
    """
    Configure logging to both file and console with rotation and formatting.

    Args:
        log_level: The logging level to use (default: logging.INFO)
    """
    # Create logs directory if it doesn't exist
    log_file = os.path.join(os.getcwd(), 'ttc_scrape.log')

    # Create formatter
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear any existing handlers
    root_logger.handlers = []

    # Create rotating file handler (10MB max size, keep 5 backup files)
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Log system info at startup
    logger = logging.getLogger("TTC Scrape Logger")
    logger.info('='*50)
    logger.info(f'Logging initiated at {
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    logger.info(f'Log file location: {log_file}')
    logger.info('='*50)
    return logger
