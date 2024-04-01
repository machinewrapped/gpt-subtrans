from PySubtitle.SubtitleError import SubtitleError


class ViewModelError(SubtitleError):
    def __init__(self, message, error = None):
        super().__init__(message, error)