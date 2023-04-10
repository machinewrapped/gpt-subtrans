
class ProjectSelection():
    def __init__(self) -> None:
        self.scenes = []
        self.batches = []
        self.subtitles = []
        self.translated = []

    def __str__(self):
        return f"{len(self.scenes)} scenes with {len(self.subtitles)} subtitles and {len(self.translated)} translations in {len(self.batches)} batches"
