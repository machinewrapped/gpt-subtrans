from os import linesep

from PySubtitleGPT.SubtitleBatch import SubtitleBatch

class SubtitleScene:
    def __init__(self):
        self.number = None
        self.context = {}
        self._batches = []

    @property
    def batches(self):
        return self._batches

    @property
    def size(self):
        return len(self._batches)

    @property
    def linecount(self):
        return sum(batch.size for batch in self.batches)

    @property
    def all_translated(self):
        return all(batch.all_translated for batch in self.batches)

    @property
    def summary(self):
        return self.GetContext('summary')

    def AddBatch(self, batch):
        self._batches.append(batch)

    def AddNewBatch(self):
        self._batches.append(SubtitleBatch())
        return self._batches[-1]

    def AddContext(self, key, value):
        if not self.context:
            self.context = {}
        self.context[key] = value

    def GetContext(self, key):
        return self.context.get(key) if self.context else None
