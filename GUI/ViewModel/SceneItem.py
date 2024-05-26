from GUI.ViewModel.BatchItem import BatchItem
from GUI.ViewModel.ViewModelError import ViewModelError
from GUI.ViewModel.ViewModelItem import ViewModelItem
from GUI.GuiHelpers import DescribeLineCount
from PySubtitle.Helpers import UpdateFields
from PySubtitle.SubtitleScene import SubtitleScene

from PySide6.QtCore import Qt

class SceneItem(ViewModelItem):
    """ Represents a scene in the view model """
    def __init__(self, scene : SubtitleScene):
        super(SceneItem, self).__init__()
        self.number = scene.number
        self.batches = {}
        self.scene_model = {
            'scene': scene.number,
            'start': scene.batches[0].txt_start,
            'end': scene.batches[-1].srt_end,
            'duration': None,
            'gap': None,
            'summary': scene.summary
        }

        # cache on demand
        self._first_line_num = None
        self._last_line_num = None

        self.setText(f"Scene {scene.number}")
        self.setData(self.scene_model, Qt.ItemDataRole.UserRole)

    @property
    def batch_count(self):
        return len(self.batches)

    @property
    def translated_batch_count(self):
        return sum(1 if batch.translated_count else 0 for batch in self.batches.values())

    @property
    def line_count(self):
        return sum(batch.line_count for batch in self.batches.values())

    @property
    def translated_count(self):
        return sum(batch.translated_count for batch in self.batches.values())

    @property
    def all_translated(self):
        return self.batches and all(b.all_translated for b in self.batches.values())

    @property
    def first_line_number(self):
        if not self.batches:
            return None

        batch_number = sorted(self.batches.keys())[0]
        return self.batches[batch_number].first_line_number if self.batches else None

    @property
    def last_line_number(self):
        if not self.batches:
            return None

        batch_number = sorted(self.batches.keys())[-1]
        return self.batches[batch_number].last_line_number if self.batches else None

    @property
    def has_errors(self):
        return self.batches and any(b.has_errors for b in self.batches.values())

    @property
    def start(self):
        return self.scene_model['start']

    @property
    def end(self):
        return self.scene_model['end']

    @property
    def duration(self):
        return self.scene_model['duration']

    @property
    def summary(self):
        return self.scene_model['summary']

    def AddBatchItem(self, batch_item : BatchItem):
        """ Insert or append a batch item to the scene """
        if batch_item.number > len(self.batches):
            self.appendRow(batch_item)
        else:
            self.insertRow(batch_item.number - 1, batch_item)

        self.Remap()

    def Update(self, update):
        """ Update the scene model with new data """
        if not isinstance(update, dict):
            raise ViewModelError(f"Expected a dictionary, got a {type(update).__name__}")

        UpdateFields(self.scene_model, update, ['summary', 'start', 'end', 'duration', 'gap'])

    def Remap(self):
        """ Rebuild the batch number map """
        batch_items = {}
        for i in range(0, self.rowCount()):
            batch_item = self.child(i, 0)
            batch_item.number = i + 1
            batch_items[batch_item.number] = batch_item

        self.batches = batch_items

    def GetContent(self):
        """ Return a dictionary of interesting scene data for UI display """
        str_translated = "All batches translated" if self.translated_batch_count == self.batch_count else f"{self.translated_batch_count} of {self.batch_count} batches translated"
        metadata = [
            "1 line" if self.line_count == 1 else f"{self.line_count} lines in {self.batch_count} batches",
            str_translated if self.translated_batch_count > 0 else None,
        ]

        return {
            'heading': f"Scene {self.number}",
            'subheading': f"Lines {self.first_line_number}-{self.last_line_number} ({self.start} -> {self.end})",
            'body': self.summary if self.summary else "\n".join([data for data in metadata if data is not None]),
            'footer': DescribeLineCount(self.line_count, self.translated_count),
            'properties': {
                'all_translated' : self.all_translated,
                'errors' : self.has_errors
            }
        }

    def __str__(self) -> str:
        content = self.GetContent()
        return f"{content['heading']}\n{content['subheading']}\n{content['body']}"