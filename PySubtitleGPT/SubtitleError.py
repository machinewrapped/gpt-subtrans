
class TranslationError(Exception):
    def __init__(self, message, translation):
        super().__init__(message)
        self.translation = translation

