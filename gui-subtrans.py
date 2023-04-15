import argparse
import logging
import os
import sys

from PySide6.QtWidgets import QApplication
from GUI.MainWindow import MainWindow
from PySubtitleGPT.Options import Options

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
    parser.add_argument('--minbatchsize', type=int, default=None, help="Minimum number of lines to consider starting a new batch")
    parser.add_argument('--maxbatchsize', type=int, default=None, help="Maximum number of lines before starting a new batch is compulsory")
    parser.add_argument('--batchthreshold', type=float, default=None, help="Number of seconds between lines to consider for batching")
    parser.add_argument('--scenethreshold', type=float, default=None, help="Number of seconds between lines to consider a new scene")
    parser.add_argument('--maxlines', type=int, default=None, help="Maximum number of batches to process")
    parser.add_argument('--theme', type=str, default=None, help="Stylesheet to load")

    args = parser.parse_args()

    arguments = {
        'api_key': args.apikey,
        'max_lines': args.maxlines,
        'rate_limit': args.ratelimit,
        'target_language': args.target_language,
        'min_batch_size': args.minbatchsize,
        'max_batch_size': args.maxbatchsize,
        'batch_threshold': args.batchthreshold,
        'scene_threshold': args.scenethreshold,
        'project': args.project and args.project.lower(),
        'theme': args.theme
    }
    
    return arguments, args.filepath

if __name__ == "__main__":
    app = QApplication(sys.argv)

    arguments, filepath = parse_arguments()

    options = Options(arguments)
    app.main_window = MainWindow( options=options, filepath=filepath)
    app.main_window.show()

    app.exec()
