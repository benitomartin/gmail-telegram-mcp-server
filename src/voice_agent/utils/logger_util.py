import logging
import sys


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
            name: The name of the logger.
            level: The logging level (default is logging.INFO).

    Returns:
            Configured logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(stream=sys.stderr)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] %(levelname)-8s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger
