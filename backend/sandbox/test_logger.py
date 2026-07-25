"""
Test script for verifying Custom Logger configuration and outputs.

Expected Behavior:
- Console: Outputs 5 log messages with distinct ANSI colors (Cyan, Green, Yellow, Red, Bold Red).
- File: Writes identical 5 log entries to backend/logs/app_YYYY-MM-DD.log without ANSI codes.
"""

from core.logger import get_logger

# Instantiate logger instance for the sandbox test module
logger = get_logger(__name__)

if __name__ == "__main__":
    # Log test messages for all 5 standard log severity levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    # Verification guidelines:
    # 1. Console Output: Verify colors match DEBUG (Cyan/Blue), INFO (Green), WARNING (Yellow), ERROR (Red), CRITICAL (Bold Red).
    # 2. File Output: Inspect backend/logs/app_YYYY-MM-DD.log to confirm entries contain timestamp, level, name, and message without ANSI codes.
