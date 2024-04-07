import os
import argparse
import logging

from PySubtitle.Helpers import ParseNames, ParseSubstitutions
from PySubtitle.Options import Options
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.SubtitleTranslator import SubtitleTranslator
from PySubtitle.TranslationProvider import TranslationProvider

provider = "Local Server"

log_path = os.path.join(os.getcwd(), 'local-subtrans.log')
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
    file_handler = logging.FileHandler(log_path, encoding='utf-8', mode='w')
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logging.getLogger('').addHandler(file_handler)
except Exception as e:
    logging.warning(f"Unable to create log file at {log_path}: {e}")

# Parse command line arguments
parser = argparse.ArgumentParser(description='Translates an SRT file using a local server')
parser.add_argument('input', help="Input SRT file path")
parser.add_argument('-o', '--output', help="Output SRT file path")
parser.add_argument('-l', '--target_language', type=str, default=None, help="The target language for the translation")
parser.add_argument('-s', '--server', type=str, default=None, help="Address of the server including port (e.g. http://localhost:1234)")
parser.add_argument('-e', '--endpoint', type=str, default=None, help="Endpoint to call on  the server (e.g. /v1/completions)")
parser.add_argument('-k', '--apikey', type=str, default=None, help="API Key, if required")

parser.add_argument('--batchthreshold', type=float, default=None, help="Number of seconds between lines to consider for batching")
parser.add_argument('--chat', action='store_true', help="Use chat format requests for the endpoint")
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
parser.add_argument('--systemmessages', action='store_true', help="Indicates that the endpoint supports system messages in chat requests")
parser.add_argument('--temperature', type=float, default=0.0, help="A higher temperature increases the random variance of translations.")
parser.add_argument('--writebackup', action='store_true', help="Write a backup of the project file when it is loaded (if it exists)")

args = parser.parse_args()

if args.debug:
    logging.getLogger('').setLevel(logging.DEBUG)
    logging.debug("Debug logging enabled")

try:
    options = Options({
        'api_key': args.apikey,
        'batch_threshold': args.batchthreshold,
        'description': args.description,
        'endpoint': args.endpoint,
        'include_original': args.includeoriginal,
        'instruction_args': args.instruction,
        'instruction_file': args.instructionfile,
        'match_partial_words': args.matchpartialwords,
        'max_batch_size': args.maxbatchsize,
        'max_context_summaries': args.maxsummaries,
        'max_lines': args.maxlines,
        'min_batch_size': args.minbatchsize,
        'movie_name': args.moviename or os.path.splitext(os.path.basename(args.input))[0],
        'names': ParseNames(args.names or args.name),
        'project': args.project and args.project.lower(),
        'provider': provider,
        'rate_limit': args.ratelimit,
        'scene_threshold': args.scenethreshold,
        'server_address': args.server,
        'substitutions': ParseSubstitutions(args.substitution),
        'supports_conversation': args.chat,
        'supports_system_messages': args.systemmessages,
        'target_language': args.target_language,
        'temperature': args.temperature,
        'write_backup': args.writebackup,
    })

    # Update provider settings with any relevant command line arguments
    translation_provider = TranslationProvider.get_provider(options)
    if not translation_provider:
        raise ValueError(f"Unable to create translation provider {options.provider}")

    if not translation_provider.ValidateSettings():
        logging.error(f"Provider settings are not valid: {translation_provider.validation_message}")
        raise ValueError(f"Invalid settings for provider {options.provider}")

    logging.info(f"Using translation provider {translation_provider.name}")

    # Load the instructions
    options.InitialiseInstructions()

    # Process the project options
    project = SubtitleProject(options)

    project.InitialiseProject(args.input, args.output, args.writebackup)
    project.UpdateProjectSettings(options)

    logging.info(f"Translating {project.subtitles.linecount} subtitles from {args.input}")

    translator = SubtitleTranslator(options, translation_provider)

    project.TranslateSubtitles(translator)

    if project.write_project:
        logging.info(f"Writing project data to {str(project.projectfile)}")
        project.WriteProjectFile()

except Exception as e:
    print("Error:", e)
    raise
