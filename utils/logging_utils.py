# ==========================================
# IMPORTS
# ==========================================
import logging
import os

# ==========================================
# CONFIGURATION
# ==========================================
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_DIR = "storage/logs"

# ==========================================
# FUNCTIONS
# ==========================================
def setup_logger(name, log_file, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    os.makedirs(DEFAULT_LOG_DIR, exist_ok=True)
    file_path = os.path.join(DEFAULT_LOG_DIR, log_file)
    
    file_handler = logging.FileHandler(file_path)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger
