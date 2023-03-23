import os
import argparse
import dotenv
import logging
from PySubtitleGPT.Helpers import ParseSubstitutions
from PySubtitleGPT.Options import Options
from PySubtitleGPT.SubtitleProject import SubtitleProject
from PySubtitleGPT.SubtitleFile import SubtitleFile

# Load environment variables from .env file
dotenv.load_dotenv()

logging_level = eval(f"logging.{os.getenv('LOG_LEVEL', 'WARNING')}")
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging_level)

# Parse command line arguments
parser = argparse.ArgumentParser(description='Translates an SRT file using ChatGPT')
parser.add_argument('input', help="Input SRT file path")
parser.add_argument('-o', '--output', help="Output SRT file path")
parser.add_argument('-l', '--target_language', type=str, default=None, help="The target language for the translation")
parser.add_argument('-m', '--moviename', type=str, default=None, help="Optionally specify the name of the movie to help the translator")
parser.add_argument('-r', '--ratelimit', type=int, default=None, help="Maximum number of batches per minute to process")
parser.add_argument('-k', '--apikey', type=str, default=None, help="Your OpenAI API Key (https://platform.openai.com/account/api-keys)")
parser.add_argument('-t', '--temperature', type=float, default=0.0, help="A higher temperature increases the random variance of translations.")
parser.add_argument('-p', '--project', type=str, default=None, help="Read or Write project file to working directory")
parser.add_argument('-s', '--substitution', action='append', type=str, default=None, help="A pair of strings separated by ::, to subsitute in source or translation")
parser.add_argument('-i', '--instruction', action='append', type=str, default=None, help="An instruction for Chat GPT about the translation")
parser.add_argument('-f', '--instructionfile', type=str, default=None, help="Name/path of a file to load GPT instructions from")
parser.add_argument('--synopsis', type=str, default=None, help="A brief synopsis of the film to give context")
parser.add_argument('--characters', type=str, default=None, help="A list of character names")
parser.add_argument('--minbatchsize', type=int, default=None, help="Minimum number of lines to consider starting a new batch")
parser.add_argument('--maxbatchsize', type=int, default=None, help="Maximum number of lines before starting a new batch is compulsory")
parser.add_argument('--batchthreshold', type=float, default=None, help="Number of seconds between lines to consider for batching")
parser.add_argument('--scenethreshold', type=float, default=None, help="Number of seconds between lines to consider a new scene")
parser.add_argument('--maxlines', type=int, default=None, help="Maximum number of batches to process")

args = parser.parse_args()

try:
    options = Options({
        'api_key': args.apikey,
        'max_lines': args.maxlines,
        'rate_limit': args.ratelimit,
        'target_language': args.target_language,
        'movie_name': args.moviename or args.input,
        'synopsis': args.synopsis,
        'characters': args.characters,
        'substitutions': ParseSubstitutions(args.substitution),
        'instruction_file': args.instructionfile,
        'instruction_args': args.instruction,
        'min_batch_size': args.minbatchsize,
        'max_batch_size': args.maxbatchsize,
        'batch_threshold': args.batchthreshold,
        'scene_threshold': args.scenethreshold,
        'project': args.project and args.project.lower()
    })

    # Process the project options
    project = SubtitleProject(options, args.input)

    # Try to load the project file if required
    if project.read_project:
        subtitles = project.ReadProjectFile()

        if subtitles:
            logging.info(f"Project file loaded, saving backup copy")
            project.WriteBackupFile(subtitles)
        else:
            logging.warning(f"Unable to read project file, starting afresh")
            subtitles = SubtitleFile(args.output)
            project.load_subtitles = True
    else:
        subtitles = SubtitleFile(args.output)

    # Try to load the subtitle file if required
    if project.load_subtitles: 
        subtitles.LoadSubtitles(args.input)

    if subtitles.has_subtitles == False:
        raise Exception(f"No subtitles to translate in {args.input}")

    logging.info(f"Translating {subtitles.linecount} subtitles from {args.input}")

    subtitles.Translate(options, project)

    if project.write_project:
        logging.info(f"Writing project data to {str(subtitles.filename)}")
        project.WriteProjectFile(subtitles)

except Exception as e:
    print("Error:", e)
    raise
