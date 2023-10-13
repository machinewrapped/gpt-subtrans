import logging
import os
from PySide6.QtCore import Qt, QModelIndex, QMutex, QMutexLocker, Signal

from PySide6.QtGui import QStandardItemModel, QStandardItem
from GUI.GuiHelpers import GetLineHeight
from GUI.ProjectViewModelUpdate import ModelUpdate
from PySubtitle import SubtitleLine

from PySubtitle.Helpers import FormatMessages, Linearise, UpdateFields
from PySubtitle.SubtitleError import SubtitleError
from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.SubtitleScene import SubtitleScene
from PySubtitle.SubtitleBatch import SubtitleBatch

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
    updatesPending = Signal()

    def __init__(self):
        super().__init__()
        self.model = {}
        self.updates = []
        self.update_lock = QMutex()

    def getRootItem(self):
        return self.invisibleRootItem()
    
    def AddUpdate(self, update):
        with QMutexLocker(self.update_lock):
            self.updates.append(update)
        self.updatesPending.emit()

    def ProcessUpdates(self):
        with QMutexLocker(self.update_lock):
            for update in self.updates:
                self.ApplyUpdate(update)
            self.updates = []

        self.layoutChanged.emit()

    def CreateModel(self, data : SubtitleFile):
        if not isinstance(data, SubtitleFile):
            raise Exception("Can only model subtitle files")

        self.model = {}

        for scene in data.scenes:
            scene_item = self.CreateSceneItem(scene)
            self.model[scene.number] = scene_item
            self.getRootItem().appendRow(scene_item)

    def CreateSceneItem(self, scene : SubtitleScene):
        scene_item = SceneItem(scene)

        for batch in scene.batches:
            batch_item : BatchItem = self.CreateBatchItem(scene.number, batch)
            scene_item.AddBatchItem(batch_item)

        return scene_item

    def CreateBatchItem(self, scene_number : int, batch : SubtitleBatch):
        batch_item = BatchItem(scene_number, batch)

        for line in batch.originals:
            batch_item.AddLineItem(False, line.number, {
                'scene': scene_number,
                'batch': batch.number,
                'start': line.srt_start,
                'end': line.srt_end,
                'text': line.text
            })

        if batch.translated:
            for line in batch.translated:
                batch_item.AddLineItem(True, line.number,  {
                    'scene': scene_number,
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
                        line = lines.get(line_number, None) if lines else None
                        if line:
                            return line

    def GetBatchNumbers(self):
        """
        Get all batch numbers for the model
        """
        batch_numbers = []
        for scene_item in self.model.values():
            for batch_item in scene_item.batches.values():
                batch_numbers.append((batch_item.scene, batch_item.number))
        return batch_numbers

    def Remap(self):
        """
        Rebuild the dictionary keys for the model
        """
        scene_items : list[SceneItem] = [ self.getRootItem().child(i, 0) for i in range(0, self.getRootItem().rowCount()) ]
        self.model = { item.number: item for item in scene_items }

        for scene_item in scene_items:
            batch_items : list[BatchItem] = [ scene_item.child(i, 0) for i in range(0, scene_item.rowCount()) ]

            for batch_number, batch_item in enumerate(batch_items, start=1):
                if batch_item.scene != scene_item.number or batch_item.number != batch_number:
                    logging.debug(f"Batch ({batch_item.scene}, {batch_item.number}) -> ({scene_item.number},{batch_item.number})")
                    batch_item.scene = scene_item.number
                    batch_item.number = batch_number
                
            scene_item.batches = { item.number: item for item in batch_items }

            for batch_item in batch_items:
                line_items : list[LineItem] = [ batch_item.child(i, 0) for i in range(0, batch_item.rowCount()) ]

                for line_item in line_items:
                    if line_item.scene != scene_item.number or line_item.batch != batch_item.number:
                        # logging.debug(f"Batch ({line_item.scene},{line_item.batch}) Line {line_item.number} -> Batch ({scene_item.number},{batch_item.number})")
                        line_item.line_model['scene'] = scene_item.number
                        line_item.line_model['batch'] = batch_item.number

                batch_item.translated = { item.number: item for item in line_items if item.is_translation }
                batch_item.originals = { item.number: item for item in line_items if not item.is_translation }

    def ApplyUpdate(self, update : ModelUpdate):
        """
        Patch the viewmodel
        """
        self.beginResetModel()
        self.blockSignals(True)

        for scene_number, scene_update in update.scenes.updates.items():
            self.UpdateScene(scene_number, scene_update)

        for key, batch_update in update.batches.updates.items():
            scene_number, batch_number = key
            self.UpdateBatch(scene_number, batch_number, batch_update)

        #TODO: Use UpdateOriginalLines
        for key, line_update in update.originals.updates.items():
            scene_number, batch_number, line_number = key
            self.UpdateOriginalLine(scene_number, batch_number, line_number, line_update)

        #TODO: Use UpdateTranslatedLines
        for key, line_update in update.translated.updates.items():
            scene_number, batch_number, line_number = key
            self.UpdateTranslatedLine(scene_number, batch_number, line_number, line_update)

        for scene_number, scene in update.scenes.replacements.items():
            self.ReplaceScene(scene)

        for key, batch in update.batches.replacements.items():
            scene_number, batch_number = key
            self.ReplaceBatch(batch)

        for scene_number in reversed(update.scenes.removals):
            self.RemoveScene(scene_number)

        for key in reversed(update.batches.removals):
            scene_number, batch_number = key
            self.RemoveBatch(scene_number, batch_number)

        for key in reversed(update.originals.removals):
            scene_number, batch_number, line_number = key
            self.RemoveOriginalLine(scene_number, batch_number, line_number)

        for key in reversed(update.translated.removals):
            scene_number, batch_number, line_number = key
            self.RemoveTranslatedLine(scene_number, batch_number, line_number)

        for scene_number, scene in update.scenes.additions.items():
            self.AddScene(scene)

        for key, batch in update.batches.additions.items():
            scene_number, batch_number = key
            self.AddBatch(batch)

        for key, line in update.originals.additions.items():
            scene_number, batch_number, line_number = key
            self.AddOriginalLine(scene_number, batch_number, line_number, line)

        for key, line in update.translated.additions.items():
            scene_number, batch_number, line_number = key
            self.AddTranslatedLine(scene_number, batch_number, line_number, line)

        # Rebuild the model dictionaries
        self.Remap()
        self.blockSignals(False)
        self.endResetModel()
    


    #############################################################################

    def AddScene(self, scene : SubtitleScene):
        logging.debug(f"Adding scene {scene.number}")
        if not isinstance(scene, SubtitleScene):
            raise ViewModelError(f"Wrong type for AddScene ({type(scene).__name__})")

        scene_item = self.CreateSceneItem(scene)

        root_item = self.getRootItem()
        insert_row = scene_item.number - 1

        self.beginInsertRows(QModelIndex(), insert_row, insert_row)
        if scene_item.number > len(self.model):
            root_item.appendRow(scene_item)
        else:
            root_item.insertRow(insert_row, scene_item)
            for i in range(0, self.rowCount()):
                root_item.child(i, 0).number = i + 1
        
        scene_items = [ root_item.child(i, 0) for i in range(0, root_item.rowCount()) ]
        self.model = { item.number: item for item in scene_items }

        self.endInsertRows()

    def ReplaceScene(self, scene):
        logging.debug(f"Replacing scene {scene.number}")
        if not isinstance(scene, SubtitleScene):
            raise ViewModelError(f"Wrong type for ReplaceScene ({type(scene).__name__})")
        
        scene_item = SceneItem(scene)
        scene_index = self.indexFromItem(self.model[scene.number]) 

        self.beginRemoveRows(QModelIndex(), scene_index.row(), scene_index.row())
        scene_item.removeRow(scene_index.row())
        self.endRemoveRows()

        self.beginInsertRows(QModelIndex(), scene_index.row(), scene_index.row())
        scene_item.insertRow(scene_index.row(), scene_item)
        self.endInsertRows()

        self.model[scene.number] = scene_item

        self.getRootItem().emitDataChanged()

    def UpdateScene(self, scene_number, scene_update : dict):
        logging.debug(f"Updating scene {scene_number}")
        scene_item : SceneItem = self.model.get(scene_number)
        if not scene_item:
            raise ViewModelError(f"Model update for unknown scene {scene_number}")

        scene_item.Update(scene_update)

        if scene_update.get('number'):
            scene_item.number = scene_update['number']

        if scene_update.get('batches'):
            for batch_number, batch_update in scene_update['batches'].items():
                self.UpdateBatch(scene_number, batch_number, batch_update)

        scene_index = self.indexFromItem(scene_item)
        self.setData(scene_index, scene_item, Qt.ItemDataRole.UserRole)

        return True

    def RemoveScene(self, scene_number):
        logging.debug(f"Removing scene {scene_number}")
        if scene_number not in self.model.keys():
            raise ViewModelError(f"Scene number {scene_number} does not exist")

        root_item = self.getRootItem()        
        scene_item = self.model.get(scene_number)
        scene_index = self.indexFromItem(scene_item)

        self.beginRemoveRows(QModelIndex(), scene_index.row(), scene_index.row())
        root_item.removeRow(scene_index.row())
        self.endRemoveRows()

        del self.model[scene_number]

    #############################################################################

    def AddBatch(self, batch : SubtitleBatch):
        logging.debug(f"Adding new batch ({batch.scene}, {batch.number})")
        if not isinstance(batch, SubtitleBatch):
            raise ViewModelError(f"Wrong type for AddBatch ({type(batch).__name__})")

        batch_item : BatchItem = self.CreateBatchItem(batch.scene, batch)

        scene_item : SceneItem = self.model.get(batch.scene)
        scene_index = self.indexFromItem(scene_item)
        insert_row = batch_item.number - 1

        self.beginInsertRows(scene_index, insert_row, insert_row)
        scene_item.AddBatchItem(batch_item)
        self.endInsertRows()

        scene_item.emitDataChanged()

    def ReplaceBatch(self, batch):
        logging.debug(f"Replacing batch ({batch.scene}, {batch.number})")
        if not isinstance(batch, SubtitleBatch):
            raise ViewModelError(f"Wrong type for ReplaceBatch ({type(batch).__name__})")

        scene_item : SceneItem = self.model[batch.scene]
        scene_index = self.indexFromItem(scene_item)
        batch_index = self.indexFromItem(scene_item.batches[batch.number])
        
        self.beginRemoveRows(scene_index, batch_index.row(), batch_index.row())
        scene_item.removeRow(batch_index.row())
        self.endRemoveRows()

        batch_item : BatchItem = self.CreateBatchItem(batch.scene, batch)

        self.beginInsertRows(scene_index, batch_index.row(), batch_index.row())
        scene_item.insertRow(batch_index.row(), batch_item)
        self.endInsertRows()

        scene_item.batches[batch.number] = batch_item
        scene_item.emitDataChanged()

    def UpdateBatch(self, scene_number, batch_number, batch_update : dict):
        logging.debug(f"Updating batch ({scene_number}, {batch_number})")
        if not isinstance(batch_update, dict):
            raise ViewModelError("Expected a patch dictionary")
        
        scene_item : SceneItem = self.model.get(scene_number)
        batch_item : BatchItem = scene_item.batches[batch_number] if scene_number else None
        if not batch_item:
            logging.error(f"Model update for unknown batch, scene {scene_number} batch {batch_number}")
            return False

        batch_item.Update(batch_update)

        if batch_update.get('number'):
            batch_item.number = batch_update['number']

        if batch_update.get('originals'):
            self.UpdateOriginalLines(scene_number, batch_number, batch_update['originals'])

        if batch_update.get('translated'):
            self.UpdateTranslatedLines(scene_number, batch_number, batch_update['translated'])

        batch_index = self.indexFromItem(batch_item)
        self.setData(batch_index, batch_item, Qt.ItemDataRole.UserRole)

        scene_item.emitDataChanged()
        return True

    def RemoveBatch(self, scene_number, batch_number):
        logging.debug(f"Removing batch ({scene_number}, {batch_number})")
        scene_item : SceneItem = self.model.get(scene_number)
        if batch_number not in scene_item.batches.keys():
            raise ViewModelError(f"Scene {scene_number} batch {batch_number} does not exist")
        
        scene_index = self.indexFromItem(scene_item)

        for i in range(0, scene_item.rowCount()):
            batch_item : BatchItem = scene_item.child(i, 0)
            if batch_item.number == batch_number:
                self.beginRemoveRows(scene_index, i, i)
                scene_item.removeRow(i)
                self.endRemoveRows()
                logging.debug(f"Removed row {i} from scene {scene_item.number}, rowCount={scene_item.rowCount()}")
                break

    #############################################################################

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

    def UpdateOriginalLine(self, scene_number, batch_number, line_number, line_update : dict):
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

    #############################################################################

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
            elif line_number in batch_item.originals.keys():
                line_model = batch_item.originals[line_number].line_model.copy()
                UpdateFields(line_model, line_update, [ 'text' ])
                batch_item.AddLineItem(True, line_number, line_model)

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

###############################################

class LineItem(QStandardItem):
    def __init__(self, is_translation, line_number, model):
        super(LineItem, self).__init__(f"Translation {line_number}" if is_translation else f"Line {line_number}")
        self.is_translation = is_translation
        self.number = line_number
        self.line_model = model
        self.height = GetLineHeight(model.get('text'))

        self.setData(self.line_model, Qt.ItemDataRole.UserRole)

    def Update(self, line_update):
        if not isinstance(line_update, dict):
            raise ViewModelError(f"Expected a dictionary, got a {type(line_update).__name__}")

        UpdateFields(self.line_model, line_update, ['start', 'end', 'text'])

        if line_update.get('number'):
            self.number = line_update['number']

        self.height = GetLineHeight(self.line_model.get('text'))

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

        # cache on demand
        self._first_line_num = None
        self._last_line_num = None

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

        self._invalidate_first_and_last()

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
        if not self._first_line_num:
            self._update_first_and_last()
        return self._first_line_num

    @property
    def last_line_number(self):
        if not self._last_line_num:
            self._update_first_and_last()
        return self._last_line_num    

    @property
    def has_errors(self):
        return True if self.batch_model.get('errors') else False

    def Update(self, update : dict):
        if not isinstance(update, dict):
            raise ViewModelError(f"Expected a dictionary, got a {type(update).__name__}")

        UpdateFields(self.batch_model, update, ['number', 'summary', 'context', 'start', 'end'])

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

    def _update_first_and_last(self):
        line_numbers = [ num for num in self.originals.keys() if num ] if self.originals else None
        self._first_line_num = min(line_numbers) if line_numbers else None
        self._last_line_num = max(line_numbers)

    def _invalidate_first_and_last(self):
        self._first_line_num = None
        self._last_line_num = None

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
        if batch_item.number > len(self.batches):
            self.appendRow(batch_item)
        else:
            self.insertRow(batch_item.number - 1, batch_item)
            for i in range(0, self.rowCount()):
                self.child(i, 0).number = i

        batch_items = [ self.child(i, 0) for i in range(0, self.rowCount()) ]
        self.batches = { item.number: item for item in batch_items }

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


