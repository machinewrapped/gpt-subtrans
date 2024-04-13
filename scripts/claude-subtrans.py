import os
import logging

from subtrans_common import *

provider = "Claude"
default_model = os.getenv('CLAUDE_MODEL') or "claude-3-haiku-20240307"

parser = CreateArgParser(f"Translates an SRT file using Anthropic's Claude AI")
parser.add_argument('-k', '--apikey', type=str, default=None, help=f"Your Anthropic API Key (https://console.anthropic.com/settings/keys)")
parser.add_argument('-m', '--model', type=str, default=None, help="The model to use for translation")
args = parser.parse_args()

logger_options = InitLogger("claude-subtrans", args.debug)

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
