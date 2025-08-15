"""Entry point functions for gpt-subtrans command line tools."""

import os
import sys
import logging

# Add the parent directory to the sys path so that modules can be found
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_path)


def gpt_subtrans():
    """Entry point for gpt-subtrans command."""
    from scripts.subtrans_common import InitLogger, CreateArgParser, CreateOptions, CreateTranslator, CreateProject
    from PySubtitle.Options import Options
    from PySubtitle.SubtitleProject import SubtitleProject
    from PySubtitle.SubtitleTranslator import SubtitleTranslator

    # We'll write separate scripts for other providers
    provider = "OpenAI"
    default_model = os.getenv('OPENAI_MODEL') or "gpt-4o"

    parser = CreateArgParser(f"Translates an SRT file using an OpenAI model")
    parser.add_argument('-k', '--apikey', type=str, default=None, help=f"Your OpenAI API Key (https://platform.openai.com/account/api-keys)")
    parser.add_argument('-b', '--apibase', type=str, default="https://api.openai.com/v1", help="API backend base address.")
    parser.add_argument('-m', '--model', type=str, default=None, help="The model to use for translation")
    parser.add_argument('--httpx', action='store_true', help="Use the httpx library for custom api_base requests. May help if you receive a 307 redirect error.")
    parser.add_argument('--proxy', type=str, default=None, help="SOCKS proxy URL (e.g., socks://127.0.0.1:1089)")
    args = parser.parse_args()

    logger_options = InitLogger("gpt-subtrans", args.debug)

    try:
        options : Options = CreateOptions(
            args,
            provider,
            use_httpx=args.httpx,
            api_base=args.apibase,
            proxy=args.proxy,
            model=args.model or default_model
        )

        # Create a project for the translation
        project : SubtitleProject = CreateProject(options, args)

        # Create a translator with the provided options
        translator : SubtitleTranslator = CreateTranslator(options)

        # Translate the subtitles
        project.TranslateSubtitles(translator)

        if project.write_project:
            logging.info(f"Writing project data to {str(project.projectfile)}")
            project.WriteProjectFile()

    except Exception as e:
        print("Error:", e)
        raise


def gui_subtrans():
    """Entry point for gui-subtrans command."""
    import sys
    import os

    # Add the parent directory to the sys path so that modules can be found
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(base_path)

    from scripts.subtrans_common import InitLogger, CreateArgParser
    from PySubtitle.Helpers.Localization import initialize_localization

    from PySide6.QtCore import QCoreApplication
    from PySide6.QtWidgets import QApplication
    from GUI.MainWindow import MainWindow

    parser = CreateArgParser("Graphical interface for GPT-Subtrans")
    parser.add_argument('--firstrun', action='store_true', help="Show the first run dialog.")
    parser.add_argument('--ui_language', type=str, default=None, help="UI language")
    args = parser.parse_args()

    # Initialise logging
    logger_options = InitLogger("gui-subtrans", args.debug)

    # Set some application properties before creating the application
    QCoreApplication.setApplicationName("GPT-Subtrans")
    QCoreApplication.setApplicationVersion("1.1.2")

    # Create the Qt application
    app = QApplication(sys.argv)

    # Initialize localization before creating the main window
    options = {
        'ui_language': args.ui_language
    }
    initialize_localization(options.get('ui_language'))

    # Create the main window
    window = MainWindow(subtitles_file=args.subtitles, firstrun=args.firstrun)
    window.show()

    # Run the application
    return app.exec()


def gemini_subtrans():
    """Entry point for gemini-subtrans command."""
    from scripts.subtrans_common import InitLogger, CreateArgParser, CreateOptions, CreateTranslator, CreateProject
    from PySubtitle.Options import Options
    from PySubtitle.SubtitleProject import SubtitleProject
    from PySubtitle.SubtitleTranslator import SubtitleTranslator

    provider = "Gemini"
    default_model = os.getenv('GEMINI_MODEL') or "gemini-2.0-flash-exp"

    parser = CreateArgParser(f"Translates an SRT file using a Gemini model")
    parser.add_argument('-k', '--apikey', type=str, default=None, help=f"Your Google Gemini API Key (https://ai.google.dev/)")
    parser.add_argument('-m', '--model', type=str, default=None, help="The model to use for translation")
    args = parser.parse_args()

    logger_options = InitLogger("gemini-subtrans", args.debug)

    try:
        options : Options = CreateOptions(
            args,
            provider,
            model=args.model or default_model
        )

        # Create a project for the translation
        project : SubtitleProject = CreateProject(options, args)

        # Create a translator with the provided options
        translator : SubtitleTranslator = CreateTranslator(options)

        # Translate the subtitles
        project.TranslateSubtitles(translator)

        if project.write_project:
            logging.info(f"Writing project data to {str(project.projectfile)}")
            project.WriteProjectFile()

    except Exception as e:
        print("Error:", e)
        raise


# For backward compatibility, create main functions
def main():
    """Default main function points to gpt_subtrans."""
    gpt_subtrans()


if __name__ == "__main__":
    main()