"""
Custom Logger Module for Application Backend.

Design Principles & Architecture:
---------------------------------
1. Built-in Python Logging Framework:
   This module utilizes Python's standard `logging` module without requiring external 
   third-party libraries (e.g., Loguru), ensuring zero extra dependencies, high performance,
   and standard library stability.

2. Comprehensive Log Level Support:
   Supports all 5 standard log severity levels:
   - DEBUG: Fine-grained diagnostic information for development and troubleshooting.
   - INFO: General operational messages describing routine application flow and state changes.
   - WARNING: Indications of potential issues or unexpected events that do not interrupt operation.
   - ERROR: Runtime errors or failures that prevent specific tasks or operations from completing.
   - CRITICAL: Severe system failures or catastrophic conditions requiring immediate action.

3. Structured Log Format:
   Each log entry captures four core attributes:
   - Timestamp (`%(asctime)s`): Precise date and time when the log event occurred (YYYY-MM-DD HH:MM:SS).
   - Log Level (`%(levelname)s`): Severity level of the log record.
   - Logger/Module Name (`%(name)s`): Name of the calling logger/module (__name__), facilitating exact source tracing.
   - Log Message (`%(message)s`): Detailed diagnostic or descriptive payload.

4. Dual Output Destinations:
   - StreamHandler (Console/Terminal): Outputs formatted log messages with ANSI color coding corresponding 
     to severity levels for enhanced visual distinction during development:
     * DEBUG: Cyan (\033[36m)
     * INFO: Green (\033[32m)
     * WARNING: Yellow (\033[33m)
     * ERROR: Red (\033[31m)
     * CRITICAL: Bold Red (\033[1;31m)
   - TimedRotatingFileHandler (Log File): Writes clean, uncolored logs to `.log` files inside the `logs/` directory at the root of `backend/`.

5. Automated Log Rotation & Maintenance:
   - Uses `logging.handlers.TimedRotatingFileHandler` to automatically rotate log files daily (`when="midnight"`).
   - File retention policy (`backupCount=7`): Automatically retains logs for up to 7 days and purges older logs to prevent excessive disk space consumption.
   - Automatically creates the target `logs/` directory if it does not exist.

6. Reusable Factory Pattern (`get_logger`):
   - Function `get_logger(name: str)` constructs and returns pre-configured Logger instances.
   - Guarantees handlers are attached only once per logger instance to eliminate duplicate output.
   - Standard application usage pattern: `logger = get_logger(__name__)`.
"""

import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from pathlib import Path

# Define base directory (backend root) and logs directory
BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"

# Ensure logs folder exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)


class ColoredConsoleFormatter(logging.Formatter):
    """
    Custom logging formatter that applies ANSI color escape sequences
    to console output based on the log severity level.
    """
    ANSI_COLORS = {
        logging.DEBUG: "\033[36m",       # Cyan (สีฟ้า)
        logging.INFO: "\033[32m",        # Green (สีเขียว)
        logging.WARNING: "\033[33m",     # Yellow (สีเหลือง)
        logging.ERROR: "\033[31m",       # Red (สีแดง)
        logging.CRITICAL: "\033[1;31m",  # Bold Red (สีแดงเข้ม/ตัวหนา)
    }
    ANSI_RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.ANSI_COLORS.get(record.levelno, self.ANSI_RESET)
        formatted_message = super().format(record)
        return f"{color}{formatted_message}{self.ANSI_RESET}"


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance supporting 5 log levels, ANSI colored console output,
    and daily rotating log file storage.

    Args:
        name (str): Name of the module or logger (typically __name__).

    Returns:
        logging.Logger: Fully configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handler registration if get_logger is invoked multiple times for the same module
    if logger.handlers:
        return logger

    # Log message format specification
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # 1. Console Stream Handler (ANSI Colored)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = ColoredConsoleFormatter(fmt=log_format, datefmt=date_format)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 2. File Handler (Timed Rotating File Handler without ANSI colors)
    today_str = datetime.now().strftime("%Y-%m-%d")
    log_filename = LOGS_DIR / f"app_{today_str}.log"

    file_handler = TimedRotatingFileHandler(
        filename=log_filename,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(fmt=log_format, datefmt=date_format)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Prevent logs from propagating to the root logger to avoid duplicate log outputs
    logger.propagate = False

    return logger
