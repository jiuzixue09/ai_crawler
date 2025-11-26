
import logging
from logging import Logger
from logging.handlers import RotatingFileHandler
import sys


def setup_logger(log_file_name: str, logging_name) -> Logger:
    logger = logging.getLogger(logging_name)
    logger.setLevel(logging.DEBUG)

    # Avoid adding handlers multiple times if setup_logger is called more than once
    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    # Console handler (stdout)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)  # show INFO+ on console
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # Rotating file handler
    fh = RotatingFileHandler(log_file_name, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    fh.setLevel(logging.DEBUG)  # record DEBUG+ to file
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger