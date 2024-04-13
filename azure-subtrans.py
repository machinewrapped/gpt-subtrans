import os
import logging

from PySubtitle.Options import create_options
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.SubtitleTranslator import SubtitleTranslator
from PySubtitle.TranslationProvider import TranslationProvider
from scripts.Common import CreateArgParser, InitLogger

# Update when newer ones are available - https://learn.microsoft.com/en-us/azure/ai-services/openai/reference
latest_azure_api_version = "2024-02-01"

provider = "Azure"
deployment_name = os.getenv('AZURE_DEPLOYMENT_NAME')
api_base = os.getenv('AZURE_API_BASE')
api_version = os.getenv('AZURE_API_VERSION', "2024-02-01")

parser = CreateArgParser(provider)
parser.add_argument('-b', '--apibase', type=str, default=None, help="API backend base address.")
parser.add_argument('-a', '--apiversion', type=str, default=None, help="Azure API version")
parser.add_argument('--deploymentname', type=str, default=None, help="Azure deployment name")
args = parser.parse_args()

logger_options = InitLogger(args.debug, provider)

try:
    options = create_options(
        args,
        provider,
        deployment_name=args.deploymentname or deployment_name,
        api_base=args.apibase or api_base,
        api_version=args.apiversion or api_version,
    )

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
