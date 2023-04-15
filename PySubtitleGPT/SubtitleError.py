
class TranslationError(Exception):
    def __init__(self, message, error = None):
        super().__init__(message)
        self.error = error

    def __str__(self) -> str:
        if self.error:
            return str(self.error)
        return super().__str__()
    
class TranslationImpossibleError(TranslationError):
    """ No chance of retry succeeding """
    def __init__(self, message, translation, error = None):
        super().__init__(message, error)
        self.translation = translation

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

class TooManyNewlinesError(TranslationError):
    def __init__(self, message, lines):
        super().__init__(message)
        self.lines = lines

class LineTooLongError(TranslationError):
    def __init__(self, message, lines):
        super().__init__(message)
        self.lines = lines

