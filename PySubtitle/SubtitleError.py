class SubtitleError(Exception):
    def __init__(self, message, error = None):
        super().__init__(message)
        self.error = error

    def __str__(self) -> str:
        if self.error:
            return str(self.error)
        return super().__str__()

class TranslationError(SubtitleError):
    def __init__(self, message, error = None):
        super().__init__(message)
        self.error = error
    
class TranslationImpossibleError(TranslationError):
    """ No chance of retry succeeding """
    def __init__(self, message, translation = None, error = None):
        super().__init__(message, error)
        self.translation = translation

class TranslationAbortedError(TranslationImpossibleError):
    def __init__(self, translation = None):
        super().__init__("Translation aborted", translation)

class TranslationFailedError(TranslationError):
    def __init__(self, message, translation, error = None):
        super().__init__(message, error)
        self.translation = translation

class NoTranslationError(TranslationError):
    def __init__(self, message, response):
        super().__init__(message)
        self.response = response

class UntranslatedLinesError(TranslationError):
    def __init__(self, message, lines):
        super().__init__(message)
        self.lines = lines

    def __str__(self) -> str:
        return str(self.args[0])
    
class UnmatchedLinesError(TranslationError):
    def __init__(self, message, lines):
        super().__init__(message)
        self.lines = lines

class EmptyLinesError(TranslationError):
    def __init__(self, message, lines):
        super().__init__(message)
        self.lines = lines

class TooManyNewlinesError(TranslationError):
    def __init__(self, message, lines):
        super().__init__(message)
        self.lines = lines

class LineTooLongError(TranslationError):
    def __init__(self, message, lines):
        super().__init__(message)
        self.lines = lines

