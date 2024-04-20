import logging
import os
from datetime import datetime

from PySubtitle.SubtitleFile import SubtitleFile

def _configure_base_logger(results_path, test_name):
    """
    Configures and returns a base logger that logs DEBUG messages to the console
    and to a general log file named after the test name.
    """
    logger = logging.getLogger(test_name)
    logger.setLevel(logging.DEBUG)

    # Creating file handler for the test log
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

    logger.info("".center(60, "-"))
    logger.info(f"Running {test_name}")
    logger.info("".center(60, "-"))
    logger.info("")

    for file in os.listdir(directory_path):
        if not file.endswith(".srt"):
            continue

        file_handler = _add_test_file_logger(logger, results_path, file, test_name)

        filepath = os.path.join(directory_path, file)

        current_time = datetime.now().strftime("%Y-%m-%d at %H:%M")
        logger.info(f"File: {filepath}")
        logger.info(f"Tested: {current_time}")
        logger.info("".center(60, "-"))

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
