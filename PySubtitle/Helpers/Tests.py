import logging
import os
from datetime import datetime

from PySubtitle.SubtitleFile import SubtitleFile

separator = "".center(60, "-")
wide_separator = "".center(120, "-")

def log_info(text: str, prefix: str = ""):
    """
    Logs a string as individual lines with an optional prefix on each line using logging.info.
    """
    for line in text.strip().split("\n"):
        logging.info(f"{prefix}{line}")

def log_error(text: str, prefix: str = ""):
    """
    Logs a string as individual lines with an optional prefix on each line using logging.error.
    """
    for line in text.strip().split("\n"):
        logging.error(f"{prefix}{line}")

def log_test_name(test_name: str):
    """
    Logs the name of the test with a separator before and after.
    """
    logging.info(separator)
    log_info(test_name.center(len(separator)))
    logging.info(separator)

def log_input_expected_result(input, expected, result):
    """
    Logs the input text, the expected result and the actual result.
    """
    log_info(str(input), prefix="".ljust(10))
    log_info(str(expected), prefix="===".ljust(10))
    log_info(str(result), prefix="-->".ljust(10))
    if expected != result:
        log_error("*** UNEXPECTED RESULT! ***", prefix="!!!".ljust(10))
    logging.info(separator)

def log_input_expected_error(input, expected_error, result):
    """
    Logs the input text, the expected error and the actual error.
    """
    log_info(str(input), prefix="".ljust(10))
    log_info(expected_error.__name__, prefix="===".ljust(10))
    if not isinstance(result, expected_error):
        log_error("*** UNEXPECTED ERROR! ***", prefix="!!!".ljust(10))
    log_info(str(result), prefix="-->".ljust(10))
    logging.info(separator)

def create_logfile(results_dir : str, log_name : str, log_level = logging.DEBUG) -> logging.FileHandler:
    """
    Creates a log file with the specified name in the specified directory and adds it to the root logger.
    """
    log_path = os.path.join(results_dir, log_name)
    file_handler = logging.FileHandler(log_path, encoding='utf-8', mode='w')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logging.getLogger('').addHandler(file_handler)
    return file_handler

def end_logfile(file_handler : logging.FileHandler):
    """
    Closes the file handler for the log file.
    """
    logging.getLogger('').removeHandler(file_handler)
    file_handler.close()

def _configure_base_logger(results_path, test_name):
    """
    Configures and returns a base logger that logs DEBUG messages to the console
    and to a general log file named after the test name.
    """
    logger = logging.getLogger(test_name)
    logger.setLevel(logging.DEBUG)

    test_log_path = os.path.join(results_path, f"{test_name}.log")
    file_handler = logging.FileHandler(test_log_path, mode='w', encoding='utf-8')
    file_formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger

def _add_test_file_logger(logger, results_path, input_filename, test_name):
    """
    Adds a file handler to log INFO level messages to a specific file named after the input file (without extension) and test name.
    """
    base_filename, _ = os.path.splitext(input_filename)
    input_log_path = os.path.join(results_path, f"{base_filename}-{test_name}.log")
    file_handler = logging.FileHandler(input_log_path, mode='w', encoding='utf-8')
    file_formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    return file_handler

def RunTestOnAllSrtFiles(run_test: callable, test_options: list[dict], directory_path: str, results_path: str = None):
    """
    Run a series of tests on all .srt files in the test_subtitles directory.
    """
    test_name = run_test.__name__

    results_path = results_path or directory_path
    os.makedirs(results_path, exist_ok=True)

    logger = _configure_base_logger(results_path, test_name)

    logger.info(separator)
    logger.info(f"Running {test_name}")
    logger.info(separator)
    logger.info("")

    for file in os.listdir(directory_path):
        if not file.endswith(".srt"):
            continue

        file_handler = _add_test_file_logger(logger, results_path, file, test_name)

        filepath = os.path.join(directory_path, file)

        current_time = datetime.now().strftime("%Y-%m-%d at %H:%M")
        logger.info(f"File: {filepath}")
        logger.info(f"Tested: {current_time}")
        logger.info(separator)

        try:
            subtitles = SubtitleFile(filepath)
            subtitles.LoadSubtitles()

            for options in test_options:
                logger.info("")
                run_test(subtitles, logger, options)

        except Exception as e:
            logger.error(f"Error processing {filepath}: {str(e)}")

        finally:
            logger.removeHandler(file_handler)


