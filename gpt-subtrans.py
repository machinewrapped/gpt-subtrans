import os
import logging

from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.SubtitleTranslator import SubtitleTranslator
from PySubtitle.TranslationProvider import TranslationProvider
from scripts.Common import CreateArgParser, CreateProject, InitLogger, CreateOptions, CreateTranslator

# We'll write separate scripts for other providers
provider = "OpenAI"
default_model = os.getenv('OPENAI_MODEL') or "gpt-3.5-turbo"

parser = CreateArgParser(f"Translates an SRT file using an OpenAI model")
parser.add_argument('-k', '--apikey', type=str, default=None, help=f"Your OpenAI API Key (https://platform.openai.com/account/api-keys)")
parser.add_argument('-b', '--apibase', type=str, default="https://api.openai.com/v1", help="API backend base address.")
parser.add_argument('-m', '--model', type=str, default=None, help="The model to use for translation")
parser.add_argument('--httpx', action='store_true', help="Use the httpx library for custom api_base requests. May help if you receive a 307 redirect error.")
args = parser.parse_args()

logger_options = InitLogger("gpt-subtrans", args.debug)

try:
    options = CreateOptions(
        args,
        provider,
        use_httpx=args.httpx,
        api_base=args.httpx,
        model=args.model or default_model
    )

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
