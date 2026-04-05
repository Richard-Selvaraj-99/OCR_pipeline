import logging
import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "app.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def get_logger(name: str):
    return logging.getLogger(name)

if __name__ == "__main__":
    logger = get_logger("test_logger")
    
    print("--- Starting Logger Test ---")
    logger.info("This is an INFO message - should appear in console and file.")
    logger.warning("This is a WARNING message!")
    logger.error("This is an ERROR message!")
    print(f"--- Test Complete. Check the '{LOG_FILE}' file. ---")