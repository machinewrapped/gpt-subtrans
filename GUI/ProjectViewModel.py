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

    def CreateFromModel(self, model):
        if model and 'scenes' in model:
            for scene_model in model['scenes']:
                scene_item = self.CreateSceneItem(scene_model, scene_model['scene'])
                self.root_item.appendRow(scene_item)

    def CreateSceneItem(self, scene_model, number):
        scene_item = SceneItem(number, scene_model)
        scene_item.setText(f"Scene {number}")

        for batch_model in scene_model['batches']:
            batch_item = self.CreateBatchItem(batch_model, batch_model['batch'])
            scene_item.appendRow(batch_item)

        return scene_item

    def CreateBatchItem(self, batch_model, number):
        batch_item = BatchItem(number, batch_model)
        batch_item.setText(f"Batch {number}")

        for subtitle_model in batch_model['subtitles']:
            subtitle_item = self.CreateSubtitleItem(subtitle_model, subtitle_model['index'])
            batch_item.appendRow(subtitle_item)

        return batch_item

    def CreateSubtitleItem(self, subtitle_model, index):
        subtitle_item = SubtitleItem(index, subtitle_model)
        subtitle_item.setText(f"Subtitle {index}")

        return subtitle_item

class SceneItem(ViewModelItem):
    def __init__(self, number, scene_model):
        super(SceneItem, self).__init__()
        self.number = number
        self.scene_model = scene_model
        self.setText(f"Scene {number}")

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
        return self.scene_model['batch_count']

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
    def __init__(self, number, batch_model):
        super(BatchItem, self).__init__(f"Batch {number}")
        self.number = number
        self.batch_model = batch_model

    @property
    def start(self):
        return self.batch_model['start']

    @property
    def end(self):
        return self.batch_model['end']

    @property
    def subtitles(self):
        return self.batch_model['subtitles']

    @property
    def translated(self):
        return self.batch_model['translated']

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
    def __init__(self, index, subtitle_model):
        super(SubtitleItem, self).__init__(f"Subtitle {index}")
        self.index = index
        self.subtitle_model = subtitle_model

    def __str__(self) -> str:
        return f"{self.index}: {self.start} --> {self.end} | {Linearise(self.text)}"

    @property
    def start(self):
        return self.subtitle_model['start']

    @property
    def end(self):
        return self.subtitle_model['end']

    @property
    def text(self):
        return self.subtitle_model['text']
    
    @property
    def translated_index(self):
        return self.subtitle_model.get('translated.index')
        
