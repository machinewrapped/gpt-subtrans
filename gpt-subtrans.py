import os
import argparse
import logging

from PySubtitle.Helpers import ParseNames, ParseSubstitutions
from PySubtitle.Options import Options
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.TranslationProvider import TranslationProvider

logging_level = eval(f"logging.{os.getenv('LOG_LEVEL', 'INFO')}")
logging.basicConfig(
    format='%(levelname)s: %(message)s', 
    level=logging_level,
    filename='gpt-subtrans.log',
    filemode='w',
    )

# Parse command line arguments
parser = argparse.ArgumentParser(description='Translates an SRT file using GPT')
parser.add_argument('input', help="Input SRT file path")
parser.add_argument('-o', '--output', help="Output SRT file path")
parser.add_argument('-l', '--target_language', type=str, default=None, help="The target language for the translation")
parser.add_argument('-p', '--provider', type=str, default=None, help="The translation provider to use")
parser.add_argument('-m', '--model', type=str, default=None, help="The model to use for translation")
parser.add_argument('-k', '--apikey', type=str, default=None, help="Your OpenAI API Key (https://platform.openai.com/account/api-keys)")
parser.add_argument('-b', '--apibase', type=str, default=None, help="API backend base address, the default value is https://api.openai.com/v1")

parser.add_argument('--batchthreshold', type=float, default=None, help="Number of seconds between lines to consider for batching")
parser.add_argument('--description', type=str, default=None, help="A brief description of the film to give context")
parser.add_argument('--includeoriginal', action='store_true', help="Include the original text in the translated subtitles")
parser.add_argument('--instruction', action='append', type=str, default=None, help="An instruction for Chat GPT about the translation")
parser.add_argument('--instructionfile', type=str, default=None, help="Name/path of a file to load GPT instructions from")
parser.add_argument('--matchpartialwords', action='store_true', help="Allow substitutions that do not match not on word boundaries")
parser.add_argument('--maxbatchsize', type=int, default=None, help="Maximum number of lines before starting a new batch is compulsory")
parser.add_argument('--maxlines', type=int, default=None, help="Maximum number of lines(subtitles) to process in this run")
parser.add_argument('--minbatchsize', type=int, default=None, help="Minimum number of lines to consider starting a new batch")
parser.add_argument('--moviename', type=str, default=None, help="Optionally specify the name of the movie to help the translator")
parser.add_argument('--name', action='append', type=str, default=None, help="A name to use verbatim in the translation")
parser.add_argument('--names', type=str, default=None, help="A list of names to use verbatim")
parser.add_argument('--project', type=str, default=None, help="Read or Write project file to working directory")
parser.add_argument('--ratelimit', type=int, default=None, help="Maximum number of batches per minute to process")
parser.add_argument('--scenethreshold', type=float, default=None, help="Number of seconds between lines to consider a new scene")
parser.add_argument('--substitution', action='append', type=str, default=None, help="A pair of strings separated by ::, to subsitute in source or translation")
parser.add_argument('--temperature', type=float, default=0.0, help="A higher temperature increases the random variance of translations.")

args = parser.parse_args()

try:
    options = Options({
        'api_base': args.apibase,
        'api_key': args.apikey,
        'batch_threshold': args.batchthreshold,
        'description': args.description,
        'include_original': args.includeoriginal,
        'instruction_args': args.instruction,
        'instruction_file': args.instructionfile,
        'match_partial_words': args.matchpartialwords,
        'max_batch_size': args.maxbatchsize,
        'max_lines': args.maxlines,
        'min_batch_size': args.minbatchsize,
        'model': args.model,
        'movie_name': args.moviename or os.path.splitext(os.path.basename(args.input))[0],
        'names': ParseNames(args.names or args.name),
        'project': args.project and args.project.lower(),
        'provider': args.provider,
        'rate_limit': args.ratelimit,
        'scene_threshold': args.scenethreshold,
        'substitutions': ParseSubstitutions(args.substitution),
        'target_language': args.target_language
    })

    # Create the translation provider
    TranslationProvider.update_provider_settings(options)

    translation_provider = TranslationProvider.get_provider(options)
    if not translation_provider:
        raise ValueError(f"Unable to create translation provider {options.provider}")

    logging.info(f"Using translation provider {translation_provider.name}")

    # Load the instructions
    options.InitialiseInstructions()

    # Process the project options
    project = SubtitleProject(options)

    project.Initialise(args.input, args.output)

    logging.info(f"Translating {project.subtitles.linecount} subtitles from {args.input}")

    translation_provider.TranslateSubtitles(project)

    if project.write_project:
        logging.info(f"Writing project data to {str(project.projectfile)}")
        project.WriteProjectFile()

except Exception as e:
    print("Error:", e)
    raise
