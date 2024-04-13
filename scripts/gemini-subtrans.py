import os
import logging

from subtrans_common import *
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.SubtitleTranslator import SubtitleTranslator

provider = "Gemini"
default_model = os.getenv('GEMINI_MODEL') or "Gemini 1.0 Pro"

parser = CreateArgParser(f"Translates an SRT file using a Google Gemini model")
parser.add_argument('-k', '--apikey', type=str, default=None, help=f"Your Gemini API Key (https://makersuite.google.com/app/apikey)")
parser.add_argument('-m', '--model', type=str, default=None, help="The model to use for translation")
args = parser.parse_args()

logger_options = InitLogger("gemini-subtrans", args.debug)

try:
    options = CreateOptions(args, provider, model=args.model or default_model)

    # Create a translator with the provided options
    translator : SubtitleTranslator = CreateTranslator(options)

    # Create a project for the translation
    project : SubtitleProject = CreateProject(options, args)

    # Translate the subtitles
    project.TranslateSubtitles(translator)

    if project.write_project:
        logging.info(f"Writing project data to {str(project.projectfile)}")
        project.WriteProjectFile()

except Exception as e:
    print("Error:", e)
    raise
