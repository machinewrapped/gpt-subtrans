import os
import logging

from PySubtitle.Options import create_options
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.SubtitleTranslator import SubtitleTranslator
from PySubtitle.TranslationProvider import TranslationProvider
from scripts.Common import CreateArgParser, InitLogger

provider = "Claude"
default_model = os.getenv('CLAUDE_MODEL') or "claude-3-haiku-20240307"

parser = CreateArgParser(provider)
parser.add_argument('-m', '--model', type=str, default=None, help="The model to use for translation")
args = parser.parse_args()

logger_options = InitLogger(args.debug, provider)

try:
    options = create_options(args, provider, model=args.model or default_model)

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
