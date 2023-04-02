import logging
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem

class ProjectViewModel(QStandardItemModel):
    def __init__(self):
        super().__init__()
        self.root_item = QStandardItem()
        self.invisibleRootItem().appendRow(self.root_item)

    def getRootItem(self):
        return self.root_item

    def createFromDataModel(self, data_model):
        if data_model and 'scenes' in data_model:
            for scene_data in data_model['scenes']:
                scene_item = self.createSceneItem(scene_data, scene_data['scene'])
                self.root_item.appendRow(scene_item)

    def createSceneItem(self, scene_data, index):
        scene_item = SceneItem(index, scene_data)
        scene_item.setText(f"Scene {index}")

        for batch_data in scene_data['batches']:
            batch_item = self.createBatchItem(batch_data, batch_data['batch'])
            scene_item.appendRow(batch_item)

        return scene_item

    def createBatchItem(self, batch_data, index):
        batch_item = BatchItem(index, batch_data)
        batch_item.setText(f"Batch {index}")

        for subtitle_data in batch_data['subtitles']:
            subtitle_item = self.createSubtitleItem(subtitle_data, subtitle_data['index'])
            batch_item.appendRow(subtitle_item)

        return batch_item

    def createSubtitleItem(self, subtitle_data, index):
        subtitle_item = SubtitleItem(index, subtitle_data)
        subtitle_item.setText(f"Subtitle {index}")

        return subtitle_item

class SceneItem(QStandardItem):
    def __init__(self, index, scene_data):
        super(SceneItem, self).__init__()
        self.index = index
        self.scene_data = scene_data
        self.setText(f"Scene {index}")

    @property
    def start(self):
        return self.scene_data['start']

    @property
    def end(self):
        return self.scene_data['end']

    @property
    def duration(self):
        return self.scene_data['duration']

    @property
    def subtitle_count(self):
        return self.scene_data['subtitle_count']

    @property
    def batch_count(self):
        return self.scene_data['batch_count']

    def getContent(self):
        return {
            'heading': f"Scene {self.index}",
            'subheading': f"{str(self.start)} -> {str(self.end)}",   # ({end - start})
            'body': f"{self.subtitle_count} subtitles in {self.batch_count} batches"
        }

    def __str__(self) -> str:
        content = self.getContent()
        return f"{content['heading']}\n{content['subheading']}\n{content['body']}"


class BatchItem(QStandardItem):
    def __init__(self, index, batch_data):
        super(BatchItem, self).__init__(f"Batch {index}")
        self.index = index
        self.batch_data = batch_data

    @property
    def start(self):
        return self.batch_data['start']

    @property
    def end(self):
        return self.batch_data['end']

    @property
    def subtitles(self):
        return self.batch_data['subtitles']

    @property
    def translated(self):
        return self.batch_data['translated']

    @property
    def subtitle_count(self):
        return len(self.subtitles)

    def getContent(self):
        return {
            'heading': f"Batch {self.index}",
            'subheading': f"{str(self.start)} -> {str(self.end)}",   # ({end - start})
            'body': f"{self.subtitle_count} subtitles"
        }
    
    def __str__(self) -> str:
        content = self.getContent()
        return f"{content['heading']}\n{content['subheading']}\n{content['body']}"

class SubtitleItem(QStandardItem):
    def __init__(self, index, subtitle_data):
        super(SubtitleItem, self).__init__(f"Subtitle {index}")
        self.index = index
        self.subtitle_data = subtitle_data

    @property
    def start(self):
        return self.subtitle_data['start']

    @property
    def end(self):
        return self.subtitle_data['end']

    @property
    def text(self):
        return self.subtitle_data['text']
        
