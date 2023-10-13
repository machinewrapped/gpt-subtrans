import logging
import os
from datetime import datetime

from PySubtitle.SubtitleBatcher import OldSubtitleBatcher, SubtitleBatcher
from PySubtitle.SubtitleFile import SubtitleFile

def configure_logger(filename, logger_name):
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

def analyze_scenes(scenes):
    num_scenes = len(scenes)
    num_batches_list = []
    largest_batch_list = []
    smallest_batch_list = []
    average_batch_size_list = []

    for scene in scenes:
        num_batches = len(scene.batches)
        batch_sizes = [batch.size for batch in scene.batches]

        largest_batch = max(batch_sizes)
        smallest_batch = min(batch_sizes)
        average_batch_size = sum(batch_sizes) / num_batches

        num_batches_list.append(num_batches)
        largest_batch_list.append(largest_batch)
        smallest_batch_list.append(smallest_batch)
        average_batch_size_list.append(average_batch_size)

    return num_scenes, num_batches_list, largest_batch_list, smallest_batch_list, average_batch_size_list

def run_test(subtitles: SubtitleFile, logger, options):
    try:
        old_batcher = OldSubtitleBatcher(options)
        old_scenes = old_batcher.BatchSubtitles(subtitles.originals)
    except Exception as e:
        raise Exception(f"Error in old_batcher.BatchSubtitles: {e}")

    try:
        new_batcher = SubtitleBatcher(options)
        new_scenes = new_batcher.BatchSubtitles(subtitles.originals)
    except Exception as e:
        raise Exception(f"Error in new_batcher.BatchSubtitles: {e}")

    if len(old_scenes) != len(new_scenes):
        raise Exception(f"Scene count mismatch (Old: {len(old_scenes)}, New: {len(new_scenes)})")

    # Analyze scenes
    old_num_scenes, old_num_batches_list, old_largest_batch_list, old_smallest_batch_list, old_avg_batch_list = analyze_scenes(old_scenes)
    new_num_scenes, new_num_batches_list, new_largest_batch_list, new_smallest_batch_list, new_avg_batch_list = analyze_scenes(new_scenes)

    logger.info(f"{f'':<25}{'Old':<10}{'New':<10}{'Delta':<10}")

    total_old_batches = sum(old_num_batches_list)
    total_new_batches = sum(new_num_batches_list)
    total_delta_batches = total_new_batches - total_old_batches

    total_old_largest = max(old_largest_batch_list)
    total_new_largest = max(new_largest_batch_list)
    total_delta_largest = total_new_largest - total_old_largest

    total_old_smallest = min(old_smallest_batch_list)
    total_new_smallest = min(new_smallest_batch_list)
    total_delta_smallest = total_new_smallest - total_old_smallest

    total_old_avg = sum(old_avg_batch_list) / old_num_scenes
    total_new_avg = sum(new_avg_batch_list) / new_num_scenes
    total_delta_avg = total_new_avg - total_old_avg

    logger.info("".center(60, "-"))
    logger.info(f"Total (min {options['min_batch_size']}, max {options['max_batch_size']}, scene {options['scene_threshold']}, batch {options['batch_threshold']})")
    logger.info("".center(60, "-"))
    logger.info(f"{'Total Batches':<25}{total_old_batches:<10}{total_new_batches:<10}{' ' if total_delta_batches == 0 else total_delta_batches:<10}")
    logger.info(f"{'Total Largest Batch':<25}{total_old_largest:<10}{total_new_largest:<10}{' ' if total_delta_largest == 0 else total_delta_largest:<10}")
    logger.info(f"{'Total Smallest Batch':<25}{total_old_smallest:<10}{total_new_smallest:<10}{' ' if total_delta_smallest == 0 else total_delta_smallest:<10}")
    logger.info(f"{'Average Batch Size':<25}{total_old_avg:<10.2f}{total_new_avg:<10.2f}{'' if abs(total_delta_avg) < 1.0 else f'{total_delta_avg:.2f}':<10}")
    logger.info("".center(60, "-"))

    for i in range(old_num_scenes):
        scene_num = i + 1

        delta_num_batches = new_num_batches_list[i] - old_num_batches_list[i]
        delta_largest_batch = new_largest_batch_list[i] - old_largest_batch_list[i]
        delta_smallest_batch = new_smallest_batch_list[i] - old_smallest_batch_list[i]
        delta_avg_batch = new_avg_batch_list[i] - old_avg_batch_list[i]

        logger.info(f"{f'-- Scene {scene_num} --':<25}")
        logger.info(f"{'Num Batches':<25}{old_num_batches_list[i]:<10}{new_num_batches_list[i]:<10}{' ' if delta_num_batches == 0 else delta_num_batches:<10}")
        logger.info(f"{'Largest Batch':<25}{old_largest_batch_list[i]:<10}{new_largest_batch_list[i]:<10}{' ' if delta_largest_batch == 0 else delta_largest_batch:<10}")
        logger.info(f"{'Smallest Batch':<25}{old_smallest_batch_list[i]:<10}{new_smallest_batch_list[i]:<10}{' ' if delta_smallest_batch == 0 else delta_smallest_batch:<10}")
        logger.info(f"{'Average Batch Size':<25}{old_avg_batch_list[i]:<10.2f}{new_avg_batch_list[i]:<10.2f}{'' if abs(delta_avg_batch) < 1.0 else f'{delta_avg_batch:.2f}':<10}")
        logger.info("")

def run_tests(directory_path, results_path):
    test_options = [
        { 'min_batch_size': 10, 'max_batch_size': 100, 'scene_threshold': 60, 'batch_threshold': 20 },
        { 'min_batch_size': 8, 'max_batch_size': 40, 'scene_threshold': 30, 'batch_threshold': 5 },
        { 'min_batch_size': 16, 'max_batch_size': 80, 'scene_threshold': 40, 'batch_threshold': 8 },
    ]

    for file in os.listdir(directory_path):
        if not file.endswith(".srt"):
            continue

        filepath = os.path.join(directory_path, file)
        result_filepath = os.path.join(results_path, f"{os.path.splitext(file)[0]}_batch_tests.txt")

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

if __name__ == "__main__":
    directory_path = os.path.join(os.getcwd(), "test_subtitles")
    run_tests(directory_path)