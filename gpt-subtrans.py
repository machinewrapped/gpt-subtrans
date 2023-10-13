import os
import argparse
import logging

from PySubtitle.Helpers import ParseCharacters, ParseSubstitutions
from PySubtitle.Options import Options
from PySubtitle.SubtitleProject import SubtitleProject

logging_level = eval(f"logging.{os.getenv('LOG_LEVEL', 'INFO')}")
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging_level)

# Parse command line arguments
parser = argparse.ArgumentParser(description='Translates an SRT file using GPT')
parser.add_argument('input', help="Input SRT file path")
parser.add_argument('-o', '--output', help="Output SRT file path")
parser.add_argument('-l', '--target_language', type=str, default=None, help="The target language for the translation")
parser.add_argument('-m', '--moviename', type=str, default=None, help="Optionally specify the name of the movie to help the translator")
parser.add_argument('-r', '--ratelimit', type=int, default=None, help="Maximum number of batches per minute to process")
parser.add_argument('-k', '--apikey', type=str, default=None, help="Your OpenAI API Key (https://platform.openai.com/account/api-keys)")
parser.add_argument('-t', '--temperature', type=float, default=0.0, help="A higher temperature increases the random variance of translations.")
parser.add_argument('-p', '--project', type=str, default=None, help="Read or Write project file to working directory")
parser.add_argument('-c', '--character', action='append', type=str, default=None, help="Read or Write project file to working directory")
parser.add_argument('-s', '--substitution', action='append', type=str, default=None, help="A pair of strings separated by ::, to subsitute in source or translation")
parser.add_argument('-i', '--instruction', action='append', type=str, default=None, help="An instruction for Chat GPT about the translation")
parser.add_argument('-f', '--instructionfile', type=str, default=None, help="Name/path of a file to load GPT instructions from")
parser.add_argument('-b', '--apibase', type=str, default=None, help="API backend base address, the default value is https://api.openai.com/v1")
parser.add_argument('--description', type=str, default=None, help="A brief description of the film to give context")
parser.add_argument('--characters', type=str, default=None, help="A list of character names")
parser.add_argument('--minbatchsize', type=int, default=None, help="Minimum number of lines to consider starting a new batch")
parser.add_argument('--maxbatchsize', type=int, default=None, help="Maximum number of lines before starting a new batch is compulsory")
parser.add_argument('--batchthreshold', type=float, default=None, help="Number of seconds between lines to consider for batching")
parser.add_argument('--scenethreshold', type=float, default=None, help="Number of seconds between lines to consider a new scene")
parser.add_argument('--maxlines', type=int, default=None, help="Maximum number of lines(subtitles) to process in this run")
parser.add_argument('--matchpartialwords', action='store_true', help="Allow substitutions that do not match not on word boundaries")
parser.add_argument('--includeoriginal', action='store_true', help="Include the original text in the translated subtitles")

args = parser.parse_args()

try:
    options = Options({
        'api_key': args.apikey,
        'api_base': args.apibase,
        'max_lines': args.maxlines,
        'rate_limit': args.ratelimit,
        'target_language': args.target_language,
        'movie_name': args.moviename or os.path.splitext(os.path.basename(args.input))[0],
        'description': args.description,
        'characters': ParseCharacters(args.characters or args.character),
        'substitutions': ParseSubstitutions(args.substitution),
        'match_partial_words': args.matchpartialwords,
        'include_original': args.includeoriginal,
        'instruction_file': args.instructionfile,
        'instruction_args': args.instruction,
        'min_batch_size': args.minbatchsize,
        'max_batch_size': args.maxbatchsize,
        'batch_threshold': args.batchthreshold,
        'scene_threshold': args.scenethreshold,
        'project': args.project and args.project.lower()
    })

    options.InitialiseInstructions()

    # Process the project options
    project = SubtitleProject(options)

    project.Initialise(args.input, args.output)

    logging.info(f"Translating {project.subtitles.linecount} subtitles from {args.input}")

    project.TranslateSubtitles()

    if project.write_project:
        logging.info(f"Writing project data to {str(project.projectfile)}")
        project.WriteProjectFile()

except Exception as e:
    print("Error:", e)
    raise
