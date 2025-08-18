import os
from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.SubtitleProcessor import SubtitleProcessor
from PySubtitle.Helpers.Tests import RunTestOnAllSrtFiles, separator

def preprocess_test(subtitles: SubtitleFile, logger, options : dict):
    try:
        preprocessor = SubtitleProcessor(options)

        test_lines = preprocessor.PreprocessSubtitles(subtitles.originals)

    except Exception as e:
        raise Exception(f"Error in PreprocessSubtitles: {e}")

    # Check if the number of lines has changed
    original_length = len(subtitles.originals)
    new_length = len(test_lines)

    logger.info(separator)
    logger.info("| {:<20} | {:<20} | {:<20} |".format("Original count", "New line count", "Delta"))
    logger.info("| {:<20} | {:<20} | {:<20} |".format(original_length, new_length, new_length - original_length))
    logger.info(separator)
    logger.info("")

    max_line_duration = options.get('max_line_duration', 0.0)
    min_line_duration = options.get('min_line_duration', 0.0)

    for line in test_lines:
        if max_line_duration > 0.0 and line.duration.total_seconds() > max_line_duration:
            logger.info(f"Line too long: {line.txt_duration}")
            logger.info(str(line))

        # if min_line_duration > 0.0 and line.duration.total_seconds() < min_line_duration:
        #     logger.info(f"Line too short: {line.srt_duration}")
        #     logger.info(str(line))
        #     logger.info("")

    logger.info(separator)

def run_tests(directory_path, results_path):
    test_options = [
        { 'max_line_duration': 5.0, 'min_line_duration': 1.0, 'min_gap': 0.1, 'min_split_chars': 4, 'whitespaces_to_newline': False, 'break_dialog_on_one_line': True, 'normalise_dialog_tags': True},
        { 'max_line_duration': 4.0, 'min_line_duration': 0.8, 'min_gap': 0.05, 'min_split_chars': 8, 'whitespaces_to_newline': True, 'break_dialog_on_one_line': False, 'normalise_dialog_tags': False}
    ]

    RunTestOnAllSrtFiles(preprocess_test, test_options, directory_path, results_path)

if __name__ == "__main__":
    directory_path = os.path.join(os.getcwd(), "test_subtitles")
    results_path = os.path.join(directory_path, "test_results")
    run_tests(directory_path)
