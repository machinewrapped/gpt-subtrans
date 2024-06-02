from datetime import timedelta
import logging

from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.Helpers.Subtitles import ResyncTranslatedLines
from PySubtitle.SubtitleLine import SubtitleLine

class SubtitleScene:
    def __init__(self, dct = None):
        dct = dct or {}
        self.number = dct.get('scene') or dct.get('number')
        self.context = dct.get('context', {})
        self._batches = dct.get('batches', [])
        self.errors = dct.get('errors', [])

    def __str__(self) -> str:
        return f"SubtitleScene {self.number} with {self.size} batches and {self.linecount} lines"

    def __repr__(self) -> str:
        return str(self)

    @property
    def batches(self) -> list[SubtitleBatch]:
        return self._batches

    @property
    def size(self):
        return len(self._batches)

    @property
    def linecount(self):
        return sum(batch.size for batch in self.batches)

    @property
    def originals(self) -> list[SubtitleLine]:
        return [ line for batch in self.batches for line in batch.originals ] if self.batches else None

    @property
    def translated(self) -> list[SubtitleLine]:
        return [ line for batch in self.batches for line in batch.translated ] if self.batches else None

    @property
    def first_line_number(self):
        return self.batches[0].first_line_number if self.batches else None

    @property
    def last_line_number(self):
        return self.batches[-1].last_line_number if self.batches else None

    @property
    def all_translated(self):
        return all(batch.all_translated for batch in self.batches)

    @property
    def any_translated(self):
        return any(batch.all_translated for batch in self.batches)

    @property
    def summary(self):
        return self.GetContext('summary')

    @summary.setter
    def summary(self, value):
        self.AddContext('summary', value)

    @batches.setter
    def batches(self, value : list[SubtitleBatch]):
        if not isinstance(value, list) or not all(isinstance(v, SubtitleBatch) for v in value):
            raise ValueError("Batches must be a list of SubtitleBatch")

        self._batches = value

    def GetBatch(self, batch_number) -> SubtitleBatch:
        for batch in self.batches:
            if batch.number == batch_number:
                return batch

        return None

    def AddBatch(self, batch):
        self._batches.append(batch)

    def AddNewBatch(self):
        batch = SubtitleBatch({
            'scene': self.number,
            'number': len(self.batches) + 1
        })
        self._batches.append(batch)
        return self._batches[-1]

    def AddContext(self, key, value):
        if not self.context:
            self.context = {}
        self.context[key] = value

    def GetContext(self, key):
        return self.context.get(key) if self.context else None

    def UpdateContext(self, update) -> bool:
        if not self.context:
            self.context = {}

        updated = False
        for key in update.keys():
            if update[key] != self.context.get(key):
                self.context[key] = update[key]
                updated = True

        return updated

    def MergeScenes(self, merged_scenes):
        """
        Merge another scene into this scene
        """
        scenes = [ self ] + merged_scenes
        self.summary = "\n".join(scene.summary for scene in scenes if scene.summary)
        self._batches = [ batch for scene in scenes for batch in scene.batches ]

        self._renumber_batches()

    def MergeBatches(self, batch_numbers : list[int]):
        """
        Merge several batches in the scene together
        """
        batch_numbers = sorted(batch_numbers)
        if batch_numbers != list(range(batch_numbers[0], batch_numbers[0] + len(batch_numbers))):
            raise ValueError("Batch numbers to be merged are not sequential")

        batches = [ batch for batch in self.batches if batch.number in batch_numbers]
        if len(batches) != len(batch_numbers):
            raise ValueError(f"Could not find batches {str(batch_numbers)} in scene {self.number}")

        merged_batch = SubtitleBatch()
        merged_batch.number = batches[0].number
        merged_batch.scene = self.number
        merged_batch.summary = "\n".join(batch.summary for batch in batches if batch.summary)

        merged_batch.originals = []
        for batch in batches:
            merged_batch.originals.extend(batch.originals)

        merged_batch.translated = []
        for batch in batches:
            if batch.translated:
                merged_batch.translated.extend(batch.translated)

        start_index = self._batches.index(batches[0])
        end_index = self._batches.index(batches[-1])

        self._batches = self._batches[:start_index] + [merged_batch] + self._batches[end_index+1:]

        self._renumber_batches()

    def SplitBatch(self, batch_number: int, line_number: int, translated_number: int = None):
        batch = self.GetBatch(batch_number)
        if not batch:
            raise ValueError("Invalid batch number")

        first_line = batch.originals[0]
        last_line = batch.originals[-1]
        if line_number <= first_line.number or line_number > last_line.number:
            raise ValueError(f"Cannot split batch {batch_number} at line {line_number}")

        split_index = next((i for i, line in enumerate(batch.originals) if line.number == line_number), -1)
        if split_index <= 0:
            raise ValueError(f"Line {line_number} not found in batch (unexpectedly)")

        new_batch = SubtitleBatch({
            'scene': batch.scene,
            'number': batch.number + 1,
            'originals': batch.originals[split_index:]
        })

        batch.originals = batch.originals[:split_index]

        if batch.translated:
            split_translated = translated_number or line_number
            translated_index = next((i for i, line in enumerate(batch.translated) if line.number == split_translated), -1)
            if translated_index >= 0:
                new_batch.translated = batch.translated[translated_index:]
                batch.translated = batch.translated[:translated_index]

                if split_translated != line_number:
                    ResyncTranslatedLines(new_batch.originals, new_batch.translated)

            elif translated_number is not None:
                logging.warning(f"Translated line number {translated_number} not found in batch translations")

            elif batch.translated[0].number >= split_translated:
                new_batch.translated = batch.translated
                batch.translated = []

        batch_index = self._batches.index(batch)
        self._batches = self._batches[:batch_index + 1] + [new_batch] + self._batches[batch_index + 1:]

        self._renumber_batches()

    def AutoSplitBatch(self, batch_number, min_size=1):
        """
        Split a list of lines in two at the optimal split point
        """
        batch = self.GetBatch(batch_number)
        if not batch:
            raise ValueError("Invalid batch number")

        midpoint = len(batch.originals) // 2
        if midpoint < min_size:
            raise ValueError("Batch is too small to split")

        best_split_index = None
        best_split_score = 0

        # Split lines according to the largest gap weighted towards the middle of the batch
        for i in range(min_size, len(batch.originals) - min_size):
            gap = batch.originals[i].start - batch.originals[i - 1].end
            proximity_to_midpoint = midpoint - abs(i - midpoint)
            split_score = proximity_to_midpoint * (gap / timedelta(milliseconds=1))

            if split_score > best_split_score:
                best_split_score = split_score
                best_split_index = i

        if best_split_index:
            split_line = batch.originals[best_split_index].number
            logging.info(f"Splitting batch {batch_number} at line {split_line}")
            self.SplitBatch(batch_number, split_line)

    def _renumber_batches(self):
        for number, batch in enumerate(self._batches, start = 1):
            batch.number = number


def UnbatchScenes(scenes : list[SubtitleScene]):
    """
    Reconstruct a sequential subtitle from multiple scenes
    """
    originals = []
    translations = []
    untranslated = []

    for scene in scenes:
        for batch in scene.batches:
            if batch.originals:
                originals.extend(batch.originals)
            if batch.translated:
                translations.extend(batch.translated)
            if batch.untranslated:
                untranslated.extend(batch.untranslated)

    return originals, translations, untranslated
