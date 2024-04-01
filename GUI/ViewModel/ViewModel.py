import logging
import os
from PySide6.QtCore import Qt, QModelIndex, QRecursiveMutex, QMutexLocker, Signal
from PySide6.QtGui import QStandardItemModel

from GUI.GuiHelpers import TimeDeltaToText
from GUI.ViewModel.BatchItem import BatchItem
from GUI.ViewModel.LineItem import LineItem
from GUI.ViewModel.SceneItem import SceneItem
from GUI.ViewModel.ViewModelError import ViewModelError

from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.SubtitleScene import SubtitleScene
from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.SubtitleLine import SubtitleLine

class ProjectViewModel(QStandardItemModel):
    updatesPending = Signal()

    def __init__(self):
        super().__init__()
        self.model = {}
        self.updates = []
        self.update_lock = QRecursiveMutex()
        self.debug_view = os.environ.get("DEBUG_MODE") == "1"

    def getRootItem(self):
        return self.invisibleRootItem()
    
    def AddUpdate(self, update : callable):
        """ Add an update to the queue and signal the main thread to process it """
        with QMutexLocker(self.update_lock):
            self.updates.append(update)
        self.updatesPending.emit()

    def ProcessUpdates(self):
        """ While there are updates in the queue, process them in sequence """
        while True:
            with QMutexLocker(self.update_lock):
                # Pop the next update from the queue until there are none left
                if not self.updates:
                    break

                update = self.updates.pop(0)

            try:
                logging.debug(f"Processing viewmodel update")
                self.ApplyUpdate(update)

            except Exception as e:
                logging.error(f"Error updating view model: {e}")
                # break?

        self.layoutChanged.emit()

    def CreateModel(self, data : SubtitleFile):
        if not isinstance(data, SubtitleFile):
            raise ValueError("Can only model subtitle files")

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
        batch_item = BatchItem(scene_number, batch, debug_view=self.debug_view)

        gap_start = None
        for line in batch.originals:
            batch_item.AddLineItem(line.number, {
                'scene': scene_number,
                'batch': batch.number,
                'start': line.srt_start,
                'end': line.srt_end,
                'duration': line.srt_duration,
                'gap': TimeDeltaToText(line.start - gap_start) if gap_start else "",
                'text': line.text
            })

            gap_start = line.end

        if batch.translated:
            for line in batch.translated:
                batch_item.AddTranslation(line.number, line.text)

        return batch_item
    
    def GetLineItem(self, line_number):
        if line_number and self.model:
            for scene_item in self.model.values():
                for batch_item in scene_item.batches.values():
                    if batch_item.first_line_number > line_number:
                        return None
                    
                    if batch_item.last_line_number >= line_number:
                        lines = batch_item.lines
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

                batch_item.lines = { item.number: item for item in line_items }

    def ApplyUpdate(self, update_function : callable):
        """
        Patch the viewmodel
        """
        try:
            update_function(self)

        except Exception as e:
            logging.error(f"Error updating viewmodel: {e}")

        # Rebuild the model dictionaries
        self.Remap()
    
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
        
        root_item = self.getRootItem()
        scene_item = SceneItem(scene)
        scene_index = self.indexFromItem(self.model[scene.number]) 

        self.beginRemoveRows(QModelIndex(), scene_index.row(), scene_index.row())
        root_item.removeRow(scene_index.row())
        self.endRemoveRows()

        self.beginInsertRows(QModelIndex(), scene_index.row(), scene_index.row())
        root_item.insertRow(scene_index.row(), scene_item)
        self.model[scene.number] = scene_item
        self.endInsertRows()

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
        del self.model[scene_number]
        self.endRemoveRows()

    #############################################################################

    def AddBatch(self, batch : SubtitleBatch):
        logging.debug(f"Adding new batch ({batch.scene}, {batch.number})")
        if not isinstance(batch, SubtitleBatch):
            raise ViewModelError(f"Wrong type for AddBatch ({type(batch).__name__})")

        batch_item : BatchItem = self.CreateBatchItem(batch.scene, batch)

        scene_item : SceneItem = self.model.get(batch.scene)
        if not scene_item:
            raise ViewModelError(f"Scene {batch.scene} not found")

        scene_index = self.indexFromItem(scene_item)
        insert_row = batch_item.number - 1

        self.beginInsertRows(scene_index, insert_row, insert_row)
        scene_item.AddBatchItem(batch_item)
        scene_item.Remap()
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

        if batch_update.get('lines'):
            self.UpdateLines(scene_number, batch_number, batch_update['lines'])

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

    def AddLine(self, scene_number, batch_number, line : SubtitleLine):
        if not isinstance(line, SubtitleLine):
            raise ViewModelError(f"Wrong type for AddLine ({type(line).__name__})")

        logging.debug(f"Adding line ({scene_number}, {batch_number}, {line.number})")

        scene_item : SceneItem = self.model.get(scene_number)
        batch_item : BatchItem = scene_item.batches[batch_number]
        if line.number in batch_item.lines.keys():
            raise ViewModelError(f"Line {line.number} already exists in {scene_number} batch {batch_number}")

        self.beginInsertRows(self.indexFromItem(batch_item), line.number - 1, line.number - 1)
        batch_item.AddLineItem(line.number, {
                'scene': scene_number,
                'batch': batch_number,
                'start': line.srt_start,
                'end': line.srt_end,
                'duration': line.srt_duration,
                'gap': None,
                'text': line.text
            })

        self.endInsertRows()

    def UpdateLine(self, scene_number, batch_number, line_number, line_update : dict):
        logging.debug(f"Updating line ({scene_number}, {batch_number}, {line_number})")
        if not isinstance(line_update, dict):
            raise ViewModelError("Expected a patch dictionary")

        scene_item : SceneItem = self.model.get(scene_number)
        batch_item : BatchItem = scene_item.batches[batch_number]
        if line_number not in batch_item.lines.keys():
            raise ViewModelError(f"Line {line_number} not found in {scene_number} batch {batch_number}")
        
        line_item : LineItem = batch_item.lines[line_number]
        line_item.Update(line_update)

    def UpdateLines(self, scene_number, batch_number, lines):
        logging.debug(f"Updating lines in ({scene_number}, {batch_number})")
        scene_item : SceneItem = self.model[scene_number]
        batch_item : BatchItem = scene_item.batches[batch_number]
        for line_number, line_update in lines.items():
            line_item : LineItem = batch_item.lines.get(line_number)
            if line_item:
                line_item.Update(line_update)
            else:
                logging.warning(f"Line {line_number} not found in batch {batch_number}")

    def RemoveLine(self, scene_number, batch_number, line_number):
        logging.debug(f"Removing line ({scene_number}, {batch_number}, {line_number})")

        scene_item : SceneItem = self.model.get(scene_number)
        batch_item : BatchItem = scene_item.batches[batch_number]
        if line_number not in batch_item.lines.keys():
            raise ViewModelError(f"Line {line_number} not found in {scene_number} batch {batch_number}")
        
        line_item = batch_item.lines[line_number]
        line_index = self.indexFromItem(line_item)
        batch_item.removeRow(line_index.row())

        del batch_item.lines[line_number]

        batch_item.emitDataChanged()

    def RemoveLines(self, scene_number, batch_number, line_numbers):
        logging.debug(f"Removing lines in ({scene_number}, {batch_number})")

        unfound_lines = []
        scene_item : SceneItem = self.model[scene_number]
        batch_item : BatchItem = scene_item.batches[batch_number]
        for line_number in reversed(line_numbers):
            if line_number in batch_item.lines.keys():
                line_item = batch_item.lines[line_number]
                line_index = self.indexFromItem(line_item)
                batch_item.removeRow(line_index.row())

                del batch_item.lines[line_number]

            else:
                unfound_lines.append(line_number)

        if unfound_lines:
            logging.warning(f"Lines {unfound_lines} not found in batch {batch_number}")

        batch_item.emitDataChanged()

###############################################

###############################################

###############################################



