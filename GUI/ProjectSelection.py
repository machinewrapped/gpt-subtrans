
class ProjectSelection():
    def __init__(self) -> None:
        self.scenes = []
        self.batches = []
        self.subtitles = []
        self.translated = []

    def __str__(self):
        if self.scenes:
            return f"{self.str_scenes} with {self.str_subtitles} and {self.str_translated} in {self.str_batches}"
        elif self.batches:
            return f"{self.str_subtitles} and {self.str_translated} in {self.str_batches}"
        elif self.translated:
            return f"{self.str_subtitles} and {self.str_translated}"
        elif self.subtitles:
            return f"{self.str_subtitles}"
        else:
            return "Nothing selected"

    @property
    def str_scenes(self):
        return self._count(len(self.scenes), "scene", "scenes")

    @property
    def str_batches(self):
        return self._count(len(self.batches), "batch", "batches")

    @property
    def str_subtitles(self):
        return self._count(len(self.subtitles), "subtitle", "subtitles")

    @property
    def str_translated(self):
        return self._count(len(self.translated), "translation", "translations")

    def _count(self, num, singular, plural):
        if num == 0:
            return f"No {plural}"
        elif num == 1:
            return f"1 {singular}"
        else:
            return f"{num} {plural}"

