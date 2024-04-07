import argparse
import logging
import os
import sys
import cProfile
from pstats import Stats

from PySide6.QtWidgets import QApplication
from GUI.MainWindow import MainWindow
from PySubtitle.Options import Options, settings_path, config_dir
from scripts.Common import InitLogger

"""
    This code ensures that Python can import modules located in the same folder as the currently executing script,
    even if the script is invoked from a different location. This would allow local, project-specific modules to be
    accessed as though they were installed in the standard Python library locations.
"""
project_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_dir)

def parse_arguments():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Translates an SRT file using GPT')
    parser.add_argument('filepath', nargs='?', help="Optional file to load on startup")
    parser.add_argument('-l', '--target_language', type=str, default=None, help="The target language for the translation")
    parser.add_argument('-p', '--provider', type=str, default=None, help="The translation provider to use")
    parser.add_argument('-m', '--model', type=str, default=None, help="The model to use for translation")
    parser.add_argument('--batchthreshold', type=float, default=None, help="Number of seconds between lines to consider for batching")
    parser.add_argument('--debug', action='store_true', help="Run with DEBUG log level")
    parser.add_argument('--firstrun', action='store_true', help="Show the first-run options dialog on launch")
    parser.add_argument('--includeoriginal', action='store_true', help="Include the original text in the translated subtitles")
    parser.add_argument('--maxbatchsize', type=int, default=None, help="Maximum number of lines before starting a new batch is compulsory")
    parser.add_argument('--maxlines', type=int, default=None, help="Maximum number of batches to process")
    parser.add_argument('--minbatchsize', type=int, default=None, help="Minimum number of lines to consider starting a new batch")
    parser.add_argument('--profile', action='store_true', help="Profile execution and write stats to the console")
    parser.add_argument('--project', type=str, default="true", help="How to process the project file (read, write, preview, reload, reparse, retranslate)")
    parser.add_argument('--ratelimit', type=int, default=None, help="Maximum number of batches per minute to process")
    parser.add_argument('--scenethreshold', type=float, default=None, help="Number of seconds between lines to consider a new scene")
    parser.add_argument('--theme', type=str, default=None, help="Stylesheet to load")

    try:
        args = parser.parse_args()
    except SystemExit as e:
        print(f"Argument error: {e}")
        raise

    logger_options = InitLogger(args.debug, "gui-subtrans")

    arguments = {
        'batch_threshold': args.batchthreshold,
        'firstrun': args.firstrun,
        'include_original': args.includeoriginal,
        'max_batch_size': args.maxbatchsize,
        'max_lines': args.maxlines,
        'min_batch_size': args.minbatchsize,
        'model': args.model,
        'profile': args.profile,
        'project': args.project,
        'provider': args.provider,
        'rate_limit': args.ratelimit,
        'scene_threshold': args.scenethreshold,
        'target_language': args.target_language,
        'theme': args.theme
    }

    return arguments, args.filepath, logger_options

def run_with_profiler(app):
    profiler = cProfile.Profile()
    profiler.enable()

    app.exec()

    profiler.disable()

    profile_path = os.path.join(config_dir, 'profile_guisubtrans.txt')
    with open(profile_path, 'w') as stream:
        stats = Stats(profiler, stream=stream)
        stats.sort_stats('tottime')
        stats.print_stats(100)

    logging.info(f"Profiling stats written to {profile_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    arguments, filepath, logger_options = parse_arguments()

    # Load default options and update with any explicit arguments
    options = Options()
    if not arguments.get('firstrun') and options.LoadSettings():
        logging.info(f"Loaded settings from {settings_path}")
    options.update(arguments)
    options.InitialiseInstructions()

    # Launch the GUI
    app.main_window = MainWindow( options=options, filepath=filepath)
    app.main_window.show()

    logging.info(f"Logging to {logger_options.log_path}")

    if arguments.get('profile'):
        run_with_profiler(app)
    else:
        app.exec()
