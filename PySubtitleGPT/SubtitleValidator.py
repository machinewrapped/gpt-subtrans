from PySubtitleGPT.Options import Options
from PySubtitleGPT.SubtitleError import LineTooLongError, NoTranslationError, TooManyNewlinesError, UnmatchedLinesError
from PySubtitleGPT.SubtitleLine import SubtitleLine

class SubtitleValidator:
    def __init__(self, options : Options) -> None:
        self.options = options

    def ValidateTranslations(self, translated : list[SubtitleLine]):
        """
        Check if the translation seems at least plausible
        """
        if not translated:
            raise NoTranslationError(f"Failed to extract any translations")
        
        max_characters = self.options.get('max_characters')
        max_newlines = self.options.get('max_newlines')

        no_number = []
        too_long = []
        too_many_newlines = []

        for line in translated:
            if not line.number:
                no_number.append(line)

            if len(line.text) > max_characters:
                too_long.append(line)

            if line.text.count('\n') > max_newlines:
                too_many_newlines.append(line)

        if no_number:
            raise UnmatchedLinesError(f"{len(no_number)} translations could not be matched with a source line", no_number)

        if too_long:
            raise LineTooLongError(f"One or more lines exceeded {max_characters} characters", too_long)

        if too_many_newlines:
            raise TooManyNewlinesError(f"One or more lines contain more than {max_newlines} newlines", too_many_newlines)
