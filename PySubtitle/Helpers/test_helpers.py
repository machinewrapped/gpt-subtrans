import logging
import os
from datetime import datetime

from PySubtitle.SubtitleFile import SubtitleFile

def configure_logger(filename : str, logger_name : str):
    """
    Configures the logger to write to the given filename.
    Returns the logger instance.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(filename, mode='w', encoding='utf-8')
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger, file_handler


def run_test_on_all_srt_files(run_test, test_options : list[dict], directory_path : str, results_path : str = None):
    """
    Run a series of tests on all .srt files in the test_subtitles directory.
    """
    results_path = results_path or directory_path
    for file in os.listdir(directory_path):
        if not file.endswith(".srt"):
            continue

        filepath = os.path.join(directory_path, file)
        result_filepath = os.path.join(results_path, f"{os.path.splitext(file)[0]}_tests.txt")

        logger, file_handler = configure_logger(result_filepath, file)

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
