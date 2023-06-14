import logging
import os
from PySide6.QtCore import Qt

from PySide6.QtGui import QStandardItemModel, QStandardItem

from PySubtitleGPT.Helpers import FormatMessages, Linearise, UpdateFields
from PySubtitleGPT.SubtitleError import TranslationError
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
    
    def GetLineItem(self, line_number, get_translated):
        if line_number and self.model:
            for scene_item in self.model.values():
                for batch_item in scene_item.batches.values():
                    if batch_item.first_line_number > line_number:
                        return None
                    
                    if batch_item.last_line_number >= line_number:
                        lines = batch_item.translated if get_translated else batch_item.originals
                        if lines:
                            for line_item in lines.values():
                                if line_item.number == line_number:
                                    return line_item

    def GetBatchNumbers(self):
        """
        Get all batch numbers for the model
        """
        batch_numbers = []
        for scene_item in self.model.values():
            for batch_item in scene_item.batches.values():
                batch_numbers.append((batch_item.scene, batch_item.number))
        return batch_numbers

    def UpdateModel(self, update):
        """
        Incrementally update the viewmodel
        """
        if not self.model:
            raise Exception("Unable to update ProjectViewModel - no model")

        for scene_number, scene_update in update.items():
            self.UpdateScene(scene_number, scene_update)

        self.layoutChanged.emit()

    def UpdateScene(self, scene_number, scene_update):
        scene_item = self.model.get(scene_number)
        if not scene_item:
            logging.error(f"Model update for unknown scene {scene_number}")
            return False

        scene_item.Update(scene_update)

        if scene_update.get('batches'):
            for batch_number, batch_update in scene_update['batches'].items():
                self.UpdateBatch(scene_number, batch_number, batch_update)

        scene_index = self.indexFromItem(scene_item)
        self.setData(scene_index, scene_item, Qt.ItemDataRole.UserRole)

        return True

    def UpdateBatch(self, scene_number, batch_number, batch_update):
        scene_item : SceneItem = self.model.get(scene_number)
        batch_item : BatchItem = scene_item.batches[batch_number] if scene_number else None
        if not batch_item:
            logging.error(f"Model update for unknown batch, scene {scene_number} batch {batch_number}")
            return False

        batch_item.Update(batch_update)

        if batch_update.get('originals'):
            self._update_originals(scene_number, batch_number, batch_update['originals'])

        if batch_update.get('translated'):
            self._update_translated(scene_number, batch_number, batch_update['translated'])

        batch_index = self.indexFromItem(batch_item)
        self.setData(batch_index, batch_item, Qt.ItemDataRole.UserRole)

        return True

    def _update_originals(self, scene_number, batch_number, lines):
        scene_item : SceneItem = self.model[scene_number]
        batch_item : BatchItem = scene_item.batches[batch_number]
        for line_number, line_update in lines.items():
            line_item : LineItem = batch_item.originals[line_number]
            line_item.Update(line_update)            

    def _update_translated(self, scene_number, batch_number, lines):
        scene_item : SceneItem = self.model[scene_number]
        batch_item : BatchItem = scene_item.batches[batch_number]
        for line_number, line_update in lines.items():
            line_item : LineItem = batch_item.translated.get(line_number)
            if line_item:
                line_item.Update(line_update)
            elif line_number in batch_item.originals.keys():
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
            'errors': self._get_errors(batch.errors)
        }

        if batch.translation and os.environ.get("DEBUG_MODE") == "1":
            self.batch_model.update({
                'response': batch.translation.text,
                'context': batch.context
            })
            if batch.translation.prompt:
                self.batch_model['messages'] = FormatMessages(batch.translation.prompt.messages)


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
    def response(self):
        return self.batch_model.get('response')
    
    @property
    def first_line_number(self):
        return min(self.originals.keys()) if self.originals else None

    @property
    def last_line_number(self):
        return max(self.originals.keys()) if self.originals else None    

    @property
    def has_errors(self):
        return True if self.batch_model.get('errors') else False

    def Update(self, update : dict):
        UpdateFields(self.batch_model, update, ['summary', 'context', 'start', 'end'])

        if 'errors' in update.keys():
            self.batch_model['errors'] = self._get_errors(update['errors'])

        if 'translation' in update.keys() and os.environ.get("DEBUG_MODE") == "1":
            translation = update['translation']
            self.batch_model.update({
                'response': translation.text
            })
            if translation.prompt:
                self.batch_model['messages'] = FormatMessages(translation.prompt.messages)
    
    def GetContent(self):
        body = "\n".join(e for e in self.batch_model.get('errors')) if self.has_errors \
            else self.summary if self.summary \
            else "\n".join([ 
                "1 line" if self.original_count == 1 else f"{self.original_count} lines",
                f"{self.translated_count} translated" if self.translated_count > 0 else "" 
            ])

        return {
            'heading': f"Batch {self.number}",
            'subheading': f"{str(self.start)} -> {str(self.end)} ({self.original_count} lines)",   # ({end - start})
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
        UpdateFields(self.scene_model, update, ['summary', 'start', 'end', 'duration'])

    def GetContent(self):
        str_translated = "All batches translated" if self.translated_batch_count == self.batch_count else f"{self.translated_batch_count} of {self.batch_count} batches translated"
        metadata = [ 
            "1 line" if self.original_count == 1 else f"{self.original_count} lines in {self.batch_count} batches", 
            str_translated if self.translated_batch_count > 0 else None,
        ]

        return {
            'heading': f"Scene {self.number}",
            'subheading': f"{self.start} -> {self.end} ({self.original_count} lines)",   # ({self.duration})
            'body': self.summary if self.summary else "\n".join([data for data in metadata if data is not None]),
            'properties': {
                'all_translated' : self.all_translated,
                'errors' : self.has_errors
            }
        }

    def __str__(self) -> str:
        content = self.GetContent()
        return f"{content['heading']}\n{content['subheading']}\n{content['body']}"


