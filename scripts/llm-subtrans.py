import logging

from subtrans_common import *
from PySubtitle.Options import Options
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.SubtitleTranslator import SubtitleTranslator

provider = "Local Server"

# Parse command line arguments
parser = CreateArgParser("Translates an SRT file using an AI model running on a local server")
parser.add_argument('-s', '--server', type=str, default=None, help="Address of the server including port (e.g. http://localhost:1234)")
parser.add_argument('-e', '--endpoint', type=str, default=None, help="Endpoint to call on  the server (e.g. /v1/completions)")
parser.add_argument('-k', '--apikey', type=str, default=None, help="API Key, if required")
parser.add_argument('-m', '--model', type=str, default=None, help="Model to use if the server allows it to be specified")
parser.add_argument('--chat', action='store_true', help="Use chat format requests for the endpoint")
parser.add_argument('--systemmessages', action='store_true', help="Indicates that the endpoint supports system messages in chat requests")
args = parser.parse_args()

logger_options = InitLogger("llm-subtrans", args.debug)

try:
    options : Options = CreateOptions(
        args,
        provider,
        api_key=args.apikey,
        endpoint=args.endpoint,
        model=args.model,
        server_address=args.server,
        supports_conversation=args.chat,
        supports_system_messages=args.systemmessages
    )

    # Create a translator with the provided options
    translator : SubtitleTranslator = CreateTranslator(options)

    # Process the project options
    project = SubtitleProject(options)

    project.InitialiseProject(args.input, args.output, args.writebackup)
    project.UpdateProjectSettings(options)

    logging.info(f"Translating {project.subtitles.linecount} subtitles from {args.input}")

    project.TranslateSubtitles(translator)

    if project.write_project:
        logging.info(f"Writing project data to {str(project.projectfile)}")
        project.WriteProjectFile()

except Exception as e:
    print("Error:", e)
    raise
