from dataclasses import dataclass
import os
import logging
from PySubtitle.Options import config_dir

@dataclass
class LoggerOptions():
    file_handler: logging.FileHandler
    log_path: str

def InitLogger(debug: bool, provider: str) -> LoggerOptions:

    log_path = os.path.join(config_dir, f"{provider}.log")

    if debug:
        logging.debug("Debug logging enabled")
    else:
        level_name = os.getenv('LOG_LEVEL', 'INFO').upper()
        logging_level = getattr(logging, level_name, logging.INFO)

    # Create console logger
    try:
        logging.basicConfig(format='%(levelname)s: %(message)s', encoding='utf-8', level=logging_level)
        logging.info("Initialising log")

    except Exception as e:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging_level)
        logging.info("Unable to write to utf-8 log, falling back to default encoding")

    # Create file handler with the same logging level
    try:
        os.makedirs(config_dir, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding='utf-8', mode='w')
        file_handler.setLevel(logging_level)
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        logging.getLogger('').addHandler(file_handler)
    except Exception as e:
        logging.warning(f"Unable to create log file at {log_path}: {e}")
    return LoggerOptions(file_handler=file_handler, log_path=log_path)