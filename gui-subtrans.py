import argparse
import logging
import os
import sys

from PySide6.QtWidgets import QApplication
from GUI.MainWindow import MainWindow
from PySubtitleGPT.Options import Options, settings_path

# This seems insane but ChatGPT told me to do it.
project_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_dir)

logging_level = eval(f"logging.{os.getenv('LOG_LEVEL', 'INFO')}")
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging_level)

def parse_arguments():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Translates an SRT file using ChatGPT')
    parser.add_argument('filepath', nargs='?', help="Optional file to load on startup")
    parser.add_argument('-l', '--target_language', type=str, default=None, help="The target language for the translation")
    parser.add_argument('-r', '--ratelimit', type=int, default=None, help="Maximum number of batches per minute to process")
    parser.add_argument('-k', '--apikey', type=str, default=None, help="Your OpenAI API Key (https://platform.openai.com/account/api-keys)")
    parser.add_argument('-p', '--project', type=str, default=None, help="Read or Write project file to working directory")
    parser.add_argument('-b', '--apibase', type=str, default=None, help="API backend base address, the default value is https://api.openai.com/v1")
    parser.add_argument('--minbatchsize', type=int, default=None, help="Minimum number of lines to consider starting a new batch")
    parser.add_argument('--maxbatchsize', type=int, default=None, help="Maximum number of lines before starting a new batch is compulsory")
    parser.add_argument('--batchthreshold', type=float, default=None, help="Number of seconds between lines to consider for batching")
    parser.add_argument('--scenethreshold', type=float, default=None, help="Number of seconds between lines to consider a new scene")
    parser.add_argument('--maxlines', type=int, default=None, help="Maximum number of batches to process")
    parser.add_argument('--theme', type=str, default=None, help="Stylesheet to load")
    parser.add_argument('--firstrun', action='store_true', help="Show the first-run options dialog on launch")
    parser.add_argument('--includeoriginal', action='store_true', help="Include the original text in the translated subtitles")

    try:
        args = parser.parse_args()
    except SystemExit as e:
        print(f"Argument error: {e}")
        raise

    arguments = {
        'api_key': args.apikey,
        'api_base': args.apibase,
        'max_lines': args.maxlines,
        'rate_limit': args.ratelimit,
        'target_language': args.target_language,
        'min_batch_size': args.minbatchsize,
        'max_batch_size': args.maxbatchsize,
        'batch_threshold': args.batchthreshold,
        'scene_threshold': args.scenethreshold,
        'project': args.project and args.project.lower() or 'true',
        'theme': args.theme,
        'firstrun': args.firstrun
    }
    
    return arguments, args.filepath

if __name__ == "__main__":
    app = QApplication(sys.argv)

    arguments, filepath = parse_arguments()

    # Load default options and update with any explicit arguments
    options = Options()
    if not arguments.get('firstrun') and options.Load():
        logging.info(f"Loaded settings from {settings_path}")
    options.update(arguments)

    # Launch the GUI
    app.main_window = MainWindow( options=options, filepath=filepath)
    app.main_window.show()

    app.exec()
