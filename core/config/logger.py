"""
logger.py

2025 Carlos Arze
Trabajo de grado
Univalle

This script is the definition of the logger. This module is responsible for logging
    messages to the console(DEVELOPMENT) and to a file(PRODUCTION).
"""
import logging
import os
from typing import Optional

class CustomLogger:
    """
    A logger class to log messages to the console or to a file.
    Uses the singleton pattern to ensure only one instance of the logger is created.
    """

    _instance = None

    def __new__(cls, log_level=logging.DEBUG, log_file=None) -> "CustomLogger":
        """
        Ensures that only one instance of the logger is created (Singleton pattern).

        :param log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        :param log_file: The path to the log file. If None, logs will be displayed on the console.
        :return: The single instance of the CustomLogger class.
        """
        if cls._instance is None:
            cls._instance = super(CustomLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self, name: str = __name__, log_level: int = logging.DEBUG, log_file: Optional[str] = None) -> None:
        """
        Initializes the logger configuration.

        :param name: The name of the logger, usually passed as __name__.
        :param log_level: The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        :param log_file: The path to the log file. If None, logs will be printed to the console.
        """
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger(name)
            self.logger.setLevel(log_level)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

            # File handler for production (if log_file is provided)
            if log_file:
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)

            # Console handler for development purposes
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def set_log_file(self, log_file: str) -> None:
        """
        Dynamically changes the log file to a new one (for special cases).

        :param log_file: The path to the new log file.
        """
        # Remove all existing handlers to avoid duplicate log entries
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        # Console handler for development purposes
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def log(self, level: int, message: str) -> None:
        """
        Logs a message with the specified log level.

        :param level: The logging level (e.g., logging.INFO).
        :param message: The message to be logged.
        """
        self.logger.log(level, message)

    def debug(self, message: str) -> None:
        """Logs a message at DEBUG level.

        :param message: The message to be logged.
        """
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """Logs a message at INFO level.

        :param message: The message to be logged.
        """
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Logs a message at WARNING level.

        :param message: The message to be logged.
        """
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Logs a message at ERROR level.

        :param message: The message to be logged.
        """
        self.logger.error(message)

    def critical(self, message: str) -> None:
        """Logs a message at CRITICAL level.

        :param message: The message to be logged.
        """
        self.logger.critical(message)
