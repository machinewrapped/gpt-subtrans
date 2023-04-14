from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem

from PySubtitleGPT.Helpers import Linearise, UpdateFields
from PySubtitleGPT.SubtitleFile import SubtitleFile
from PySubtitleGPT.SubtitleScene import SubtitleScene
from PySubtitleGPT.SubtitleBatch import SubtitleBatch
from PySubtitleGPT.Subtitle import Subtitle

class ViewModelItem(QStandardItem):
    def GetContent(self):
        return {
            'heading': "Item Heading",
            'subheading': "Optional Subheading",
            'body': "Body Content"
        }

class ProjectViewModel(QStandardItemModel):
    def __init__(self):
        super().__init__()
        self.model = {}
        self.root_item = QStandardItem()
        self.invisibleRootItem().appendRow(self.root_item)

    def getRootItem(self):
        return self.root_item

    def CreateModel(self, data : SubtitleFile):
        if not isinstance(data, SubtitleFile):
            raise Exception("Can only model subtitle files")

        self.model = {}

        for scene in data.scenes:
            scene_item = self.CreateSceneItem(scene)
            self.model[scene.number] = scene_item
            self.root_item.appendRow(scene_item)

    def CreateSceneItem(self, scene : SubtitleScene):
        scene_item = SceneItem(scene)

        for batch in scene.batches:
            batch_item : BatchItem = self.CreateBatchItem(scene, batch)
            scene_item.AddBatchItem(batch_item)

        return scene_item

    def CreateBatchItem(self, scene : SubtitleScene, batch : SubtitleBatch):
        batch_item = BatchItem(scene.number, batch)

        for subtitle in batch.subtitles:
            subtitle_item : SubtitleItem = SubtitleItem(batch, subtitle, False)
            batch_item.AddSubtitleItem(subtitle_item)

        if batch.translated:
            for subtitle in batch.translated:
                subtitle_item : SubtitleItem = SubtitleItem(batch, subtitle, True)
                batch_item.AddSubtitleItem(subtitle_item)

        return batch_item

    def UpdateScene(self, scene):
        scene_number = scene['number']
        for i in range(self.rowCount()):
            scene_item : SceneItem = self.item(i)
            if isinstance(scene_item, SceneItem) and scene_item.number == scene_number:
                scene_item.Update(scene)

                if scene.get('batches'):
                    for batch in scene.get('batches'):
                        self.UpdateBatch(batch)

    def UpdateBatch(self, batch):
        scene_number = batch['scene']
        batch_number = batch['batch']
        root = self.getRootItem()
        for i in range(root.rowCount()):
            scene_item = root.child(i)
            if isinstance(scene_item, SceneItem) and scene_item.number == scene_number:
                for j in range(scene_item.rowCount()):
                    batch_item = scene_item.child(j)
                    if isinstance(batch_item, BatchItem) and batch_item.number == batch_number:
                        batch_item.Update(batch)
                        item_index = self.indexFromItem(batch_item)
                        self.setData(item_index, batch_item, Qt.ItemDataRole.DisplayRole)
                        return True
        return False

###############################################

class SubtitleItem(QStandardItem):
    def __init__(self, batch : SubtitleBatch, subtitle : Subtitle, is_translation : bool):
        super(SubtitleItem, self).__init__(f"Subtitle {subtitle.index}")
        self.is_translation = is_translation
        self.number = subtitle.index
        self.subtitle_model = {
            'scene': batch.scene,
            'batch': batch.number,
            'index': subtitle.index,
            'start': str(subtitle.start),
            'end': str(subtitle.end),
            'text': str(subtitle.text)
        }

        self.setData(self.subtitle_model, Qt.ItemDataRole.UserRole)
        if is_translation:
            self.setText(f"Translation {subtitle.index}")

    def __str__(self) -> str:
        return f"{self.number}: {self.start} --> {self.end} | {Linearise(self.text)}"

    def __repr__(self) -> str:
        return f"{self.number}: {self.start} --> {self.end}"

    @property
    def start(self):
        return self.subtitle_model['start']

    @property
    def end(self):
        return self.subtitle_model['end']

    @property
    def text(self):
        return self.subtitle_model['text']

###############################################

class BatchItem(ViewModelItem):
    def __init__(self, scene_number, batch):
        super(BatchItem, self).__init__(f"Scene {scene_number}, batch {batch.number}")
        self.scene = scene_number
        self.number = batch.number
        self.subtitles = {}
        self.translated = {}
        self.batch_model = {
            'start': str(batch.subtitles[0].start),
            'end': str(batch.subtitles[-1].end),
            'summary': batch.summary,
            'context': batch.context,
        }
        self.setData(self.batch_model, Qt.ItemDataRole.UserRole)

    def AddSubtitleItem(self, subtitle_item : SubtitleItem):
        self.appendRow(subtitle_item)
        if subtitle_item.is_translation:
            self.translated[subtitle_item.number] = subtitle_item
        else:
            self.subtitles[subtitle_item.number] = subtitle_item

    @property
    def start(self):
        return self.batch_model['start']

    @property
    def end(self):
        return self.batch_model['end']

    @property
    def subtitle_count(self):
        return len(self.subtitles)
    
    @property
    def context(self):
        return self.batch_model.get('context')
    
    @property
    def summary(self):
        return self.batch_model.get('summary')

    def GetContent(self):
        metadata = [ 
            "1 subtitle" if self.subtitle_count == 1 else f"{self.subtitle_count} subtitles", 
        ]

        return {
            'heading': f"Batch {self.number}",
            'subheading': f"{str(self.start)} -> {str(self.end)}",   # ({end - start})
            'body': self.summary if self.summary else "\n".join([data for data in metadata if data is not None])
        }
    
    def Update(self, update):
        self.batch_model.update(update)
    
    def __str__(self) -> str:
        content = self.GetContent()
        return f"{content['heading']}\n{content['subheading']}\n{content['body']}"

###############################################

class SceneItem(ViewModelItem):
    def __init__(self, scene : SubtitleScene):
        super(SceneItem, self).__init__()
        self.number = scene.number
        self.batches = {}
        self.scene_model = {
            'scene': scene.number,
            'start': scene.batches[0].start,
            'end': scene.batches[-1].end,
            'duration': None,
            'subtitle_count': sum(batch.size for batch in scene.batches),
        }
        self.setText(f"Scene {scene.number}")
        self.setData(self.scene_model, Qt.ItemDataRole.UserRole)

    def AddBatchItem(self, batch_item : BatchItem):
        self.batches[batch_item.number] = batch_item
        self.appendRow(batch_item)

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
    def subtitle_count(self):
        return self.scene_model['subtitle_count']

    @property
    def batch_count(self):
        return len(self.batches)

    def GetContent(self):
        return {
            'heading': f"Scene {self.number}",
            'subheading': f"{str(self.start)} -> {str(self.end)}",   # ({end - start})
            'body': f"{self.subtitle_count} subtitles in {self.batch_count} batches"
        }

    def Update(self, update):
        UpdateFields(self.scene_model, update, ['summary', 'context', 'start', 'end'])

    def __str__(self) -> str:
        content = self.GetContent()
        return f"{content['heading']}\n{content['subheading']}\n{content['body']}"


