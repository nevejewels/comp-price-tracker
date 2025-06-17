import logging
import os
from datetime import datetime

def setup_logger(name="diamond_logger", level=logging.INFO):
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent adding duplicate handlers
    if logger.handlers:
        return logger

    # Create log directory based on date
    log_dir = os.path.join(os.getcwd(), "files", "log")
    os.makedirs(log_dir, exist_ok=True)

    log_filename = datetime.now().strftime("%Y-%m-%d") + ".log"
    log_path = os.path.join(log_dir, log_filename)

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
