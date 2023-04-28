import logging
from PySide6.QtCore import Qt

from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySubtitleGPT import SubtitleLine

from PySubtitleGPT.Helpers import Linearise, UpdateFields
from PySubtitleGPT.SubtitleError import SubtitleError
from PySubtitleGPT.SubtitleFile import SubtitleFile
from PySubtitleGPT.SubtitleScene import SubtitleScene
from PySubtitleGPT.SubtitleBatch import SubtitleBatch

class ViewModelItem(QStandardItem):
    def GetContent(self):
        return {
            'heading': "Item Heading",
            'subheading': "Optional Subheading",
            'body': "Body Content",
            'properties': {}
        }

class ViewModelError(SubtitleError):
    def __init__(self, message, error = None):
        super().__init__(message, error)

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

        for line in batch.originals:
            batch_item.AddLineItem(False, line.number, {
                'scene': scene.number,
                'batch': batch.number,
                'start': line.srt_start,
                'end': line.srt_end,
                'text': line.text
            })

        if batch.translated:
            for line in batch.translated:
                batch_item.AddLineItem(True, line.number,  {
                    'scene': scene.number,
                    'batch': batch.number,
                    'start': line.srt_start,
                    'end': line.srt_end,
                    'text': line.text
                })

        return batch_item

    def AddScene(self, scene : SubtitleScene):
        logging.debug(f"Adding scene {scene.number}")
        if not isinstance(scene, SubtitleScene):
            raise ViewModelError(f"Wrong type for AddScene ({type(scene).__name__})")
        
        if scene.number in self.model.keys():
            raise ViewModelError(f"Scene number {scene.number} already exists")

        scene_item = SceneItem(scene)
        self.model[scene.number] = scene_item
        self.root_item.appendRow(scene_item)

    def RemoveScene(self, scene_number):
        logging.debug(f"Removing scene {scene_number}")
        if scene_number not in self.model.keys():
            raise ViewModelError(f"Scene number {scene_number} does not exist")
        
        scene_item = self.model.get(scene_number)
        scene_index = self.indexFromItem(scene_item)
        self.root_item.removeRow(scene_index.row())

        del self.model[scene_number]

    def UpdateScene(self, scene_number, scene_update):
        logging.debug(f"Updating scene {scene_number}")
        scene_item : SceneItem = self.model.get(scene_number)
        if not scene_item:
            raise ViewModelError(f"Model update for unknown scene {scene_number}")

        scene_item.Update(scene_update)

        if scene_update.get('batches'):
            for batch_number, batch_update in scene_update['batches'].items():
                self.UpdateBatch(scene_number, batch_number, batch_update)

        scene_index = self.indexFromItem(scene_item)
        self.setData(scene_index, scene_item, Qt.ItemDataRole.UserRole)

        return True

    def AddBatch(self, batch : SubtitleBatch):
        logging.debug(f"Adding new batch ({batch.scene}, {batch.number})")
        if not isinstance(batch, SubtitleBatch):
            raise ViewModelError(f"Wrong type for AddBatch ({type(batch).__name__})")

        scene_item : SceneItem = self.model.get(batch.scene)
        if batch.number in scene_item.keys():
            raise ViewModelError(f"Scene {batch.scene} batch {batch.number} already exists")

        batch_item = BatchItem(batch.scene, batch)
        scene_item.AddBatchItem(batch_item)

    def RemoveBatch(self, scene_number, batch_number):
        logging.debug(f"Removing batch ({scene_number}, {batch_number})")
        scene_item : SceneItem = self.model.get(scene_number)
        if batch_number not in scene_item.batches.keys():
            raise ViewModelError(f"Scene {scene_number} batch {batch_number} does not exist")
        
        batch_item = scene_item.batches[batch_number]
        batch_index = self.indexFromItem(batch_item)
        scene_item.removeRow(batch_index.row())

        del scene_item.batches[batch_number]

    def UpdateBatch(self, scene_number, batch_number, batch_update):
        logging.debug(f"Updating batch ({scene_number}, {batch_number})")
        if not isinstance(batch_update, dict):
            raise ViewModelError("Expected a patch dictionary")
        
        scene_item : SceneItem = self.model.get(scene_number)
        batch_item : BatchItem = scene_item.batches[batch_number] if scene_number else None
        if not batch_item:
            logging.error(f"Model update for unknown batch, scene {scene_number} batch {batch_number}")
            return False

        batch_item.Update(batch_update)

        if batch_update.get('originals'):
            self.UpdateOriginalLines(scene_number, batch_number, batch_update['originals'])

        if batch_update.get('translated'):
            self.UpdateTranslatedLines(scene_number, batch_number, batch_update['translated'])

        batch_index = self.indexFromItem(batch_item)
        self.setData(batch_index, batch_item, Qt.ItemDataRole.UserRole)

        return True

    def AddOriginalLine(self, scene_number, batch_number, line : SubtitleLine):
        if not isinstance(line, SubtitleLine):
            raise ViewModelError(f"Wrong type for AddOriginalLine ({type(line).__name__})")

        logging.debug(f"Adding original line ({scene_number}, {batch_number}, {line.number})")

        scene_item : SceneItem = self.model.get(scene_number)
        batch_item : BatchItem = scene_item.batches[batch_number]
        if line.number in batch_item.originals.keys():
            raise ViewModelError(f"Line {line.number} already exists in {scene_number} batch {batch_number}")

        batch_item.AddLineItem(False, line.number, {
                'scene': scene_number,
                'batch': batch_number,
                'start': line.srt_start,
                'end': line.srt_end,
                'text': line.text
            })

    def RemoveOriginalLine(self, scene_number, batch_number, line_number):
        logging.debug(f"Removing original line ({scene_number}, {batch_number}, {line_number})")

        scene_item : SceneItem = self.model.get(scene_number)
        batch_item : BatchItem = scene_item.batches[batch_number]
        if line_number not in batch_item.originals.keys():
            raise ViewModelError(f"Line {line_number} not found in {scene_number} batch {batch_number}")
        
        line_item = batch_item.originals[line_number]
        line_index = self.indexFromItem(line_item)
        batch_item.removeRow(line_index.row())

        del batch_item.originals[line_number]

    def UpdateOriginalLine(self, scene_number, batch_number, line_number, line_update):
        logging.debug(f"Updating original line ({scene_number}, {batch_number}, {line_number})")
        if not isinstance(line_update, dict):
            raise ViewModelError("Expected a patch dictionary")

        scene_item : SceneItem = self.model.get(scene_number)
        batch_item : BatchItem = scene_item.batches[batch_number]
        if line_number not in batch_item.originals.keys():
            raise ViewModelError(f"Line {line_number} not found in {scene_number} batch {batch_number}")
        
        line_item : LineItem = batch_item.originals[line_number]
        line_item.Update(line_update)

    def UpdateOriginalLines(self, scene_number, batch_number, lines):
        logging.debug(f"Updating original lines in ({scene_number}, {batch_number})")
        scene_item : SceneItem = self.model[scene_number]
        batch_item : BatchItem = scene_item.batches[batch_number]
        for line_number, line_update in lines.items():
            line_item : LineItem = batch_item.originals[line_number]
            line_item.Update(line_update)            


    def AddTranslatedLine(self, scene_number, batch_number, line : SubtitleLine):
        if not isinstance(line, SubtitleLine):
            raise ViewModelError(f"Wrong type for AddTranslatedLine ({type(line).__name__})")

        logging.debug(f"Adding translated line ({scene_number}, {batch_number}, {line.number})")

        scene_item : SceneItem = self.model.get(scene_number)
        batch_item : BatchItem = scene_item.batches[batch_number]
        if line.number in batch_item.translated.keys():
            # Not too worried if this happens, TBH
            raise ViewModelError(f"Line {line.number} already exists in {scene_number} batch {batch_number}")

        batch_item.AddLineItem(True, line.number, {
                'scene': scene_number,
                'batch': batch_number,
                'start': line.srt_start,
                'end': line.srt_end,
                'text': line.text
            })

    def RemoveTranslatedLine(self, scene_number, batch_number, line_number):
        logging.debug(f"Removing translated line ({scene_number}, {batch_number}, {line_number})")

        scene_item : SceneItem = self.model.get(scene_number)
        batch_item : BatchItem = scene_item.batches[batch_number]
        if line_number not in batch_item.translated.keys():
            raise ViewModelError(f"Translated line {line_number} not found in {scene_number} batch {batch_number}")
        
        line_item = batch_item.translated[line_number]
        line_index = self.indexFromItem(line_item)
        batch_item.removeRow(line_index.row())

        del batch_item.translated[line_number]

    def UpdateTranslatedLine(self, scene_number, batch_number, line_number, line_update):
        logging.debug(f"Updating translated line ({scene_number}, {batch_number}, {line_number})")

        scene_item : SceneItem = self.model.get(scene_number)
        batch_item : BatchItem = scene_item.batches[batch_number]
        if line_number not in batch_item.translated.keys():
            raise ViewModelError(f"Translated line {line_number} not found in {scene_number} batch {batch_number}")
        
        line_item : LineItem = batch_item.translated[line_number]
        line_item.Update(line_update)

    def UpdateTranslatedLines(self, scene_number, batch_number, lines):
        logging.debug(f"Updating translated lines in ({scene_number}, {batch_number})")

        scene_item : SceneItem = self.model[scene_number]
        batch_item : BatchItem = scene_item.batches[batch_number]
        for line_number, line_update in lines.items():
            line_item : LineItem = batch_item.translated.get(line_number)
            if line_item:
                line_item.Update(line_update)
            else:
                line_model = batch_item.originals[line_number].line_model.copy()
                UpdateFields(line_model, line_update, [ 'text' ])
                batch_item.AddLineItem(True, line_number, line_model)

###############################################

class LineItem(QStandardItem):
    def __init__(self, is_translation, line_number, model):
        super(LineItem, self).__init__(f"Translation {line_number}" if is_translation else f"Line {line_number}")
        self.is_translation = is_translation
        self.number = line_number
        self.line_model = model

        self.setData(self.line_model, Qt.ItemDataRole.UserRole)

    def Update(self, line_update):
        if not isinstance(line_update, dict):
            raise ViewModelError(f"Expected a dictionary, got a {type(line_update).__name__}")

        UpdateFields(self.line_model, line_update, ['start', 'end', 'text'])
        self.setData(self.line_model, Qt.ItemDataRole.UserRole)

    def __str__(self) -> str:
        return f"{self.number}: {self.start} --> {self.end} | {Linearise(self.text)}"

    def __repr__(self) -> str:
        return f"{self.number}: {self.start} --> {self.end}"

    @property
    def start(self):
        return self.line_model['start']

    @property
    def end(self):
        return self.line_model['end']

    @property
    def text(self):
        return self.line_model['text']
    
    @property
    def scene(self):
        return self.line_model.get('scene')
    
    @property
    def batch(self):
        return self.line_model.get('batch')

###############################################

class BatchItem(ViewModelItem):
    def __init__(self, scene_number, batch : SubtitleBatch):
        super(BatchItem, self).__init__(f"Scene {scene_number}, batch {batch.number}")
        self.scene = scene_number
        self.number = batch.number
        self.originals = {}
        self.translated = {}
        self.batch_model = {
            'start': batch.srt_start,
            'end': batch.srt_end,
            'summary': batch.summary,
            'context': batch.context,
            'errors': self._get_errors(batch.errors)
        }
        self.setData(self.batch_model, Qt.ItemDataRole.UserRole)

    def AddLineItem(self, is_translation : bool, line_number : int, model : dict):
        line_item : LineItem = LineItem(is_translation, line_number, model)
        self.appendRow(line_item)

        if line_item.is_translation:
            self.translated[line_number] = line_item
        else:
            self.originals[line_number] = line_item

    @property
    def original_count(self):
        return len(self.originals)
    
    @property
    def translated_count(self):
        return len(self.translated)
    
    @property
    def all_translated(self):
        return self.translated_count == self.original_count
    
    @property
    def start(self):
        return self.batch_model['start']

    @property
    def end(self):
        return self.batch_model['end']

    @property
    def context(self):
        return self.batch_model.get('context')
    
    @property
    def summary(self):
        return self.batch_model.get('summary')
    
    @property
    def has_errors(self):
        return True if self.batch_model.get('errors') else False

    def Update(self, update : dict):
        if not isinstance(update, dict):
            raise ViewModelError(f"Expected a dictionary, got a {type(update).__name__}")

        UpdateFields(self.batch_model, update, ['summary', 'context', 'start', 'end'])
    
    def GetContent(self):
        body = "\n".join(e for e in self.batch_model.get('errors')) if self.has_errors \
            else self.summary if self.summary \
            else "\n".join([ 
                "1 line" if self.original_count == 1 else f"{self.original_count} lines",
                f"{self.translated_count} translated" if self.translated_count > 0 else "" 
            ])

        return {
            'heading': f"Batch {self.number}",
            'subheading': f"{str(self.start)} -> {str(self.end)}",   # ({end - start})
            'body': body,
            'properties': {
                'all_translated' : self.all_translated,
                'errors' : self.has_errors
            }
        }
    
    def _get_errors(self, errors):
        if errors:
            if all(isinstance(e, Exception) for e in errors):
                return [ str(e) for e in errors ]
            if all(isinstance(e, dict) for e in errors):
                return [ e.get('problem') for e in errors if e.get('problem') ]
        return []
    
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
            'start': scene.batches[0].srt_start,
            'end': scene.batches[-1].srt_end,
            'duration': None,
            'summary': scene.summary
        }
        self.setText(f"Scene {scene.number}")
        self.setData(self.scene_model, Qt.ItemDataRole.UserRole)

    def AddBatchItem(self, batch_item : BatchItem):
        self.batches[batch_item.number] = batch_item
        self.appendRow(batch_item)

    @property
    def batch_count(self):
        return len(self.batches)
    
    @property
    def translated_batch_count(self):
        return sum(1 if batch.translated else 0 for batch in self.batches.values())

    @property
    def original_count(self):
        return sum(batch.original_count for batch in self.batches.values())
    
    @property
    def translated_count(self):
        return sum(batch.translated_count for batch in self.batches.values())
    
    @property
    def all_translated(self):
        return self.batches and all(b.all_translated for b in self.batches.values())

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

    def Update(self, update):
        if not isinstance(update, dict):
            raise ViewModelError(f"Expected a dictionary, got a {type(update).__name__}")

        UpdateFields(self.scene_model, update, ['summary', 'start', 'end', 'duration'])

    def GetContent(self):
        str_translated = "All batches translated" if self.translated_batch_count == self.batch_count else f"{self.translated_batch_count} of {self.batch_count} batches translated"
        metadata = [ 
            "1 line" if self.original_count == 1 else f"{self.original_count} lines in {self.batch_count} batches", 
            str_translated if self.translated_batch_count > 0 else None,
        ]

        return {
            'heading': f"Scene {self.number}",
            'subheading': f"{self.start} -> {self.end}",   # ({self.duration})
            'body': self.summary if self.summary else "\n".join([data for data in metadata if data is not None]),
            'properties': {
                'all_translated' : self.all_translated,
                'errors' : self.has_errors
            }
        }

    def __str__(self) -> str:
        content = self.GetContent()
        return f"{content['heading']}\n{content['subheading']}\n{content['body']}"


