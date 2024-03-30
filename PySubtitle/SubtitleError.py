class SubtitleError(Exception):
    def __init__(self, message, error = None):
        super().__init__(message)
        self.error = error
        self.message = message

    def __str__(self) -> str:
        if self.error:
            return str(self.error)
        elif self.message:
            return self.message
        return super().__str__()

class NoProviderError(SubtitleError):
    def __init__(self):
        super().__init__(f"Provider not specified in options")

class ProviderError(SubtitleError):
    def __init__(self, message, provider = None):
        super().__init__(message)
        self.provider = provider
 
class ProviderConfigurationError(ProviderError):
    def __init__(self, message, provider = None, error = None):
        super().__init__(message, provider)
        self.error = error

class TranslationError(SubtitleError):
    def __init__(self, message, translation = None, error = None):
        super().__init__(message)
        self.translation = translation
        self.error = error

class TranslationAbortedError(TranslationError):
    def __init__(self):
        super().__init__("Translation aborted")

class TranslationImpossibleError(TranslationError):
    """ No chance of retry succeeding """
    def __init__(self, message, error = None):
        super().__init__(message, error)

class TranslationResponseError(TranslationError):
    def __init__(self, message, response):
        super().__init__(message)
        self.response = response

class NoTranslationError(TranslationError):
    def __init__(self, message, translation = None):
        super().__init__(message=message, translation=translation)

class TranslationValidationError(TranslationError):
    def __init__(self, message, lines, translation):
        super().__init__(message, translation)
        self.lines = lines or []

class UntranslatedLinesError(TranslationValidationError):
    def __init__(self, message, lines = None, translation = None):
        super().__init__(message, lines=lines, translation=translation)

class UnmatchedLinesError(TranslationValidationError):
    def __init__(self, message, lines = None, translation = None):
        super().__init__(message, lines=lines, translation=translation)

class EmptyLinesError(TranslationValidationError):
    def __init__(self, message, lines = None, translation = None):
        super().__init__(message, lines=lines, translation=translation)

class TooManyNewlinesError(TranslationValidationError):
    def __init__(self, message, lines = None, translation = None):
        super().__init__(message, lines=lines, translation=translation)

class LineTooLongError(TranslationValidationError):
    def __init__(self, message, lines = None, translation = None):
        super().__init__(message, lines=lines, translation=translation)
 
