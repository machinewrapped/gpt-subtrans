from argparse import ArgumentParser
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

_api_key_information_urls = {
    """ Information for each of the provider API-keys """
    "Gemini": "https://makersuite.google.com/app/apikey",
    "Azure": "",
    "OpenAI": "https://platform.openai.com/account/api-keys",
    "Claude": "https://console.anthropic.com/settings/keys"
}

def CreateArgParser(provider: str) -> ArgumentParser:
    """ Create new arg parser and parse shared command line arguments between models """
    parser = ArgumentParser(description=f"Translates an SRT file using an {provider} model")
    parser.add_argument('input', help="Input SRT file path")
    parser.add_argument('-o', '--output', help="Output SRT file path")
    parser.add_argument('-l', '--target_language', type=str, default=None, help="The target language for the translation")
    parser.add_argument('-k', '--apikey', type=str, default=None, help=f"Your {provider} API Key ({_api_key_information_urls[provider]})")
    parser.add_argument('--batchthreshold', type=float, default=None, help="Number of seconds between lines to consider for batching")
    parser.add_argument('--debug', action='store_true', help="Run with DEBUG log level")
    parser.add_argument('--description', type=str, default=None, help="A brief description of the film to give context")
    parser.add_argument('--includeoriginal', action='store_true', help="Include the original text in the translated subtitles")
    parser.add_argument('--instruction', action='append', type=str, default=None, help="An instruction for the AI translator")
    parser.add_argument('--instructionfile', type=str, default=None, help="Name/path of a file to load instructions from")
    parser.add_argument('--matchpartialwords', action='store_true', help="Allow substitutions that do not match not on word boundaries")
    parser.add_argument('--maxbatchsize', type=int, default=None, help="Maximum number of lines before starting a new batch is compulsory")
    parser.add_argument('--maxlines', type=int, default=None, help="Maximum number of lines(subtitles) to process in this run")
    parser.add_argument('--maxsummaries', type=int, default=None, help="Maximum number of context summaries to provide with each batch")
    parser.add_argument('--minbatchsize', type=int, default=None, help="Minimum number of lines to consider starting a new batch")
    parser.add_argument('--moviename', type=str, default=None, help="Optionally specify the name of the movie to help the translator")
    parser.add_argument('--name', action='append', type=str, default=None, help="A name to use verbatim in the translation")
    parser.add_argument('--names', type=str, default=None, help="A list of names to use verbatim")
    parser.add_argument('--project', type=str, default=None, help="Read or Write project file to working directory")
    parser.add_argument('--ratelimit', type=int, default=None, help="Maximum number of batches per minute to process")
    parser.add_argument('--scenethreshold', type=float, default=None, help="Number of seconds between lines to consider a new scene")
    parser.add_argument('--substitution', action='append', type=str, default=None, help="A pair of strings separated by ::, to subsitute in source or translation")
    parser.add_argument('--temperature', type=float, default=0.0, help="A higher temperature increases the random variance of translations.")
    parser.add_argument('--writebackup', action='store_true', help="Write a backup of the project file when it is loaded (if it exists)")
    return parser