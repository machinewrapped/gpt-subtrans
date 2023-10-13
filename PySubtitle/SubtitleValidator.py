from PySubtitle.Options import Options
from PySubtitle.SubtitleError import EmptyLinesError, LineTooLongError, NoTranslationError, TooManyNewlinesError, UnmatchedLinesError
from PySubtitle.SubtitleLine import SubtitleLine

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
        no_text = []
        too_long = []
        too_many_newlines = []

        for line in translated:
            if not line.number:
                no_number.append(line)

            if not line.text:
                no_text.append(line)
                continue

            if len(line.text) > max_characters:
                too_long.append(line)

            if line.text.count('\n') > max_newlines:
                too_many_newlines.append(line)

        if no_number:
            raise UnmatchedLinesError(f"{len(no_number)} translations could not be matched with a source line", no_number)

        if no_text:
            raise EmptyLinesError(f"{len(no_text)} translations returned a blank line", no_text)

        if too_long:
            raise LineTooLongError(f"One or more lines exceeded {max_characters} characters", too_long)

        if too_many_newlines:
            raise TooManyNewlinesError(f"One or more lines contain more than {max_newlines} newlines", too_many_newlines)
