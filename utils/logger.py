from datetime import datetime
from logging.handlers import RotatingFileHandler
import logging


def setup_logger(
    log_path: str = "log.log",
    log_level: int = logging.INFO,
    logger_name: str = "default"
) -> logging.Logger:
    """
    Configures and returns a logger instance.

    Args:
        log_path (str): Path to the log file.
        log_level (int): Logging level (e.g., logging.INFO, logging.DEBUG).
        logger_name (str): Name of the logger instance.

    Returns:
        logging.Logger: Configured logger instance.
    """
    # Check if logger already exists to avoid duplicate handlers
    logger = logging.getLogger(logger_name)
    if logger.hasHandlers():
        return logger

    # Set the logger level
    logger.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Create rotating file handler
    file_handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Log system info at startup
    logger.info('=' * 50)
    logger.info(f'Logging initiated at {
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    logger.info(f"Log file location: {log_path}")
    logger.info('=' * 50)

    return logger
