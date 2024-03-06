from PySubtitle.Options import Options
from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.SubtitleError import EmptyLinesError, LineTooLongError, NoTranslationError, TooManyNewlinesError, UnmatchedLinesError, UntranslatedLinesError
from PySubtitle.SubtitleLine import SubtitleLine

class SubtitleValidator:
    def __init__(self, options : Options) -> None:
        self.options = options

    def ValidateBatch(self, batch : SubtitleBatch):
        """
        Check if the batch seems at least plausible
        """
        errors = []
        if batch.translated:
            if not batch.all_translated:
                errors.append(UntranslatedLinesError(f"No translation found for {len(batch.originals) - len(batch.translated)} lines"))

            try:
                errors.extend(self.ValidateTranslations(batch.translated))

            except Exception as e:
                errors.append(e)

        batch.errors = errors

    def ValidateTranslations(self, translated : list[SubtitleLine]):
        """
        Check if the translation seems at least plausible
        """
        if not translated:
            return [ NoTranslationError(f"Failed to extract any translations") ]
        
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

        errors = []

        if no_number:
            errors.append(UnmatchedLinesError(f"{len(no_number)} translations could not be matched with a source line", no_number))

        if no_text:
            errors.append(EmptyLinesError(f"{len(no_text)} translations returned a blank line", no_text))

        if too_long:
            errors.append(LineTooLongError(f"One or more lines exceeded {max_characters} characters", too_long))

        if too_many_newlines:
            errors.append(TooManyNewlinesError(f"One or more lines contain more than {max_newlines} newlines", too_many_newlines))
        
        return errors
