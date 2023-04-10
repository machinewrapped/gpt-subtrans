from PySide6.QtGui import QStandardItemModel, QStandardItem

from PySubtitleGPT.Helpers import Linearise

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
        self.root_item = QStandardItem()
        self.invisibleRootItem().appendRow(self.root_item)

    def getRootItem(self):
        return self.root_item

    def CreateFromDataModel(self, data_model):
        if data_model and 'scenes' in data_model:
            for scene_data in data_model['scenes']:
                scene_item = self.CreateSceneItem(scene_data, scene_data['scene'])
                self.root_item.appendRow(scene_item)

    def CreateSceneItem(self, scene_data, number):
        scene_item = SceneItem(number, scene_data)
        scene_item.setText(f"Scene {number}")

        for batch_data in scene_data['batches']:
            batch_item = self.CreateBatchItem(batch_data, batch_data['batch'])
            scene_item.appendRow(batch_item)

        return scene_item

    def CreateBatchItem(self, batch_data, number):
        batch_item = BatchItem(number, batch_data)
        batch_item.setText(f"Batch {number}")

        for subtitle_data in batch_data['subtitles']:
            subtitle_item = self.CreateSubtitleItem(subtitle_data, subtitle_data['index'])
            batch_item.appendRow(subtitle_item)

        return batch_item

    def CreateSubtitleItem(self, subtitle_data, index):
        subtitle_item = SubtitleItem(index, subtitle_data)
        subtitle_item.setText(f"Subtitle {index}")

        return subtitle_item

class SceneItem(ViewModelItem):
    def __init__(self, number, scene_data):
        super(SceneItem, self).__init__()
        self.number = number
        self.scene_data = scene_data
        self.setText(f"Scene {number}")

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

    def GetContent(self):
        return {
            'heading': f"Scene {self.number}",
            'subheading': f"{str(self.start)} -> {str(self.end)}",   # ({end - start})
            'body': f"{self.subtitle_count} subtitles in {self.batch_count} batches"
        }

    def __str__(self) -> str:
        content = self.GetContent()
        return f"{content['heading']}\n{content['subheading']}\n{content['body']}"


class BatchItem(ViewModelItem):
    def __init__(self, number, batch_data):
        super(BatchItem, self).__init__(f"Batch {number}")
        self.number = number
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
    
    @property
    def context(self):
        return self.batch_data.get('context')
    
    @property
    def summary(self):
        return self.batch_data.get('summary')

    def GetContent(self):
        metadata = [ 
            "1 subtitle" if self.subtitle_count == 1 else f"{self.subtitle_count} subtitles", 
            self.summary
        ]

        return {
            'heading': f"Batch {self.number}",
            'subheading': f"{str(self.start)} -> {str(self.end)}",   # ({end - start})
            'body': "\n".join([data for data in metadata if data is not None])
        }
    
    def __str__(self) -> str:
        content = self.GetContent()
        return f"{content['heading']}\n{content['subheading']}\n{content['body']}"

class SubtitleItem(QStandardItem):
    def __init__(self, index, subtitle_data):
        super(SubtitleItem, self).__init__(f"Subtitle {index}")
        self.index = index
        self.subtitle_data = subtitle_data

    def __str__(self) -> str:
        return f"{self.index}: {self.start} --> {self.end} | {Linearise(self.text)}"

    @property
    def start(self):
        return self.subtitle_data['start']

    @property
    def end(self):
        return self.subtitle_data['end']

    @property
    def text(self):
        return self.subtitle_data['text']
    
    @property
    def translated_index(self):
        return self.subtitle_data.get('translated.index')
        
