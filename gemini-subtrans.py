import os
import argparse
import logging

from PySubtitle.Options import create_options
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.SubtitleTranslator import SubtitleTranslator
from PySubtitle.TranslationProvider import TranslationProvider
from scripts.Common import InitLogger

provider = "Gemini"
default_model = os.getenv('GEMINI_MODEL') or "Gemini 1.0 Pro"

# Parse command line arguments
parser = argparse.ArgumentParser(description='Translates an SRT file using Google Gemini')
parser.add_argument('input', help="Input SRT file path")
parser.add_argument('-o', '--output', help="Output SRT file path")
parser.add_argument('-l', '--target_language', type=str, default=None, help="The target language for the translation")
parser.add_argument('-m', '--model', type=str, default=None, help="The model to use for translation")
parser.add_argument('-k', '--apikey', type=str, default=None, help="Your Google Gemini API Key (https://makersuite.google.com/app/apikey)")

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

args = parser.parse_args()

logger_options = InitLogger(args.debug, provider)

try:
    options = create_options(args, default_model, provider)

    # Update provider settings with any relevant command line arguments
    translation_provider = TranslationProvider.get_provider(options)
    if not translation_provider:
        raise ValueError(f"Unable to create translation provider {options.provider}")

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
