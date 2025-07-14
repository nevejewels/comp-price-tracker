import time
import logging

# Configure the logger
logging.basicConfig(
    level=logging.INFO,  # You can change to DEBUG, WARNING, etc.
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("task.log"),  # Log to a file
        logging.StreamHandler()           # Also print to console
    ]
)

logger = logging.getLogger(__name__)

logger.info("Start task")

for i in range(10):
    logger.info(f"Task iteration {i + 1}")
    # Simulate some work
    time.sleep(1)
