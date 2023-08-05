from itertools import groupby
from PySide6.QtCore import Qt

from GUI.ProjectViewModel import BatchItem, SceneItem

class SelectionScene:
    def __init__(self, scene : SceneItem, selected : bool = True) -> None:
        self.number = scene.number
        self.selected = selected

    def __getitem__(self, index):
        return self.batches[index]
    
    def __setitem__(self, index, value):
        self.batches[index] = value

    def __str__(self) -> str:
        return f"scene {self.number} [*]" if self.selected else f"scene {self.number}"
    
    def __repr__(self) -> str:
        return str(self)

class SelectionBatch:
    def __init__(self, batch : BatchItem, selected : bool = True) -> None:
        self.scene = batch.scene
        self.number = batch.number
        self.selected = selected

    def __str__(self) -> str:
        str = f"scene {self.scene}:batch {self.number}"
        return f"{str} [*]" if self.selected else str
    
    def __repr__(self) -> str:
        return str(self)

class SelectionLine:
    def __init__(self, scene: int, batch: int, number: int, selected : bool) -> None:
        self.scene = scene
        self.batch = batch
        self.number = number
        self.selected = selected

    def __str__(self) -> str:
        str = f"scene {self.scene}:batch {self.batch}:line {self.number}"
        return f"{str} [*]" if self.selected else str
    
    def __repr__(self) -> str:
        return str(self)

#########################################################################

class ProjectSelection():
    def __init__(self) -> None:
        self.scenes = {}
        self.batches = {}
        self.originals = {}
        self.translated = {}

    @property
    def scene_numbers(self) -> list[int]:
        return sorted([ number for number in self.scenes.keys() ])
    
    @property
    def selected_scenes(self) -> list[SelectionScene]:
        return [ scene for scene in self.scenes.values() if scene.selected]
    
    @property
    def batch_numbers(self) -> list[(int,int)]:
        return sorted([ (batch.scene, batch.number) for batch in self.batches.values() ])

    @property
    def selected_batches(self) -> list[SelectionBatch]:
        return [ batch for batch in self.batches.values() if batch.selected]

    @property
    def original_lines(self) -> list[SelectionLine]:
        return sorted([ number for number in self.originals.keys() if number is not None ])
    
    @property 
    def selected_originals(self) -> list[SelectionLine]:
        return [line for line in self.originals.values() if line.selected ]

    @property
    def translated_lines(self) -> list[SelectionLine]:
        return sorted([ number for number in self.translated.keys() ])

    @property 
    def selected_translated(self) -> list[SelectionLine]:
        return [line for line in self.translated.values() if line.selected ]

    def Any(self) -> bool:
        return self.scene_numbers or self.batch_numbers or self.original_lines or self.translated_lines
    
    def AnyScenes(self) -> bool:
        return True if self.selected_scenes else False
    
    def OnlyScenes(self) -> bool:
        return self.selected_scenes and not (self.selected_batches or self.selected_originals or self.selected_translated)
    
    def AnyBatches(self) -> bool:
        return True if self.selected_batches else False

    def OnlyBatches(self) -> bool:
        return self.selected_batches  and not (self.selected_scenes or self.selected_originals or self.selected_translated)

    def AnyLines(self) -> bool:
        return self.selected_originals or self.selected_translated
    
    def AllLinesInSameBatch(self) -> bool:
        """
        Are all selected lines part of the same batch?
        """
        originals = self.selected_originals
        translated = self.selected_translated
        return all(line.batch == originals[0].batch for line in originals) and all(line.batch == translated[0].batch for line in translated)

    def MatchingLines(self) -> bool:
        """
        Are the same original and translated lines selected?
        """
        return self.selected_originals == self.selected_translated

    def MultipleSelected(self, max = None) -> bool:
        """
        Is more than one scene, batch or line selected?
        """
        if max and len(self.selected_scenes) > max and len(self.selected_batches) > max and len(self.selected_originals) > max and len(self.selected_translated) > max:
            return False

        return len(self.selected_scenes) > 1 or len(self.selected_batches) > 1 or len(self.selected_originals) > 1 or len(self.selected_translated) > 1

    def IsContiguous(self) -> bool:
        """
        Are all selected scenes, batches and lines contiguous?
        """
        scene_numbers = sorted(scene.number for scene in self.selected_scenes)
        if scene_numbers and scene_numbers != list(range(scene_numbers[0], scene_numbers[0] + len(scene_numbers))):
            return False

        if not all(batch.scene == self.selected_batches[0].scene for batch in self.selected_batches):
            return False

        batch_numbers = sorted(batch.number for batch in self.selected_batches)
        if batch_numbers and batch_numbers != list(range(batch_numbers[0], batch_numbers[0] + len(batch_numbers))):
            return False

        if not all(batch.scene == self.selected_batches[0].scene for batch in self.selected_batches):
            return False

        line_numbers = sorted(line.number for line in self.selected_originals if line.number)
        if line_numbers and line_numbers != list(range(line_numbers[0], line_numbers[0] + len(line_numbers))):
            return False

        line_numbers = sorted(line.number for line in self.selected_translated if line.number)
        if line_numbers and line_numbers != list(range(line_numbers[0], line_numbers[0] + len(line_numbers))):
            return False

        return True
    
    def IsFirstInBatchSelected(self) -> bool:
        """
        Check whether the first line of any batch is selected
        """
        for scene, batch in self.batch_numbers:
            first_line = next((line for line in self.originals.values() if line.scene == scene and line.batch == batch), None)
            if first_line and first_line.selected:
                return True

            first_translated = next((line for line in self.translated.values() if line.scene == scene and line.batch == batch), None)
            if first_translated and first_translated.selected:
                return True

        return False
    
    def IsFirstOrLastInBatchSelected(self) -> bool:
        """
        Check whether the first or last line of any batch is selected
        """
        line_dict = {}
        for line in list(self.originals.values()) + list(self.translated.values()):
            key = (line.scene, line.batch, line.number)
            if key in line_dict:
                line_dict[key].selected = line_dict[key].selected or line.selected
            else:
                line_dict[key] = line
        
        for batch_lines in groupby(sorted(line_dict.values(), key=lambda x: (x.scene, x.batch, x.number)), key=lambda x: (x.scene, x.batch)):
            batch_lines = list(batch_lines[1])
            if batch_lines[0].selected or batch_lines[-1].selected:
                return True
        
        return False
    
    def IsFirstInSceneSelected(self) -> bool:
        """
        Check whether the first or last batch of any scene is selected
        """
        return next((batch.number for batch in self.selected_batches if batch.number == 1), False) and True
    
    def IsFirstOrLastInSceneSelected(self) -> bool:
        """
        Check whether the first or last batch of any scene is selected
        """
        scene_batches = {}
        for scene in self.scenes:
            scene_batches[scene] = [batch for batch in self.batches if batch[0] == scene]

        for batch in self.selected_batches:
            if batch.number == 1 or batch.number == scene_batches[batch][-1][1]:
                return True

        return False

    def GetHierarchy(self) -> dict:
        """
        Hierarchical representation of selected lines/batches/scenes
        """
        scenes = {}
        
        for scene in self.selected_scenes:
            scenes[scene.number] = {}
        for batch in self.selected_batches:
            scene = scenes[batch.scene] = scenes.get(batch.scene) or {}
            scene[batch.number] = { 'originals': {}, 'translated': {} }

        for line in self.selected_originals:
            scene = scenes[line.scene] = scenes.get(line.scene) or {}
            batch = scene[line.batch] = scene.get(line.batch) or { 'originals': {}, 'translated': {} }
            batch['originals'][line.number] = line

        for line in self.selected_translated:
            scene = scenes[line.scene] = scenes.get(line.scene) or {}
            batch = scene[line.batch] = scene.get(line.batch) or { 'originals': {}, 'translated': {} }
            batch['translated'][line.number] = line

        return scenes

    def AppendItem(self, model, index, selected : bool = True):
        """
        Accumulated selected batches, scenes and lines
        """
        item = model.data(index, role=Qt.ItemDataRole.UserRole)

        if isinstance(item, SceneItem):
            if selected or not item.number in self.scenes.keys():
                self.scenes[item.number] = SelectionScene(item, selected)

                children = [ model.index(i, 0, index) for i in range(model.rowCount(index))]
                for child_index in children:
                    self.AppendItem(model, child_index, False)

        elif isinstance(item, BatchItem):
            key = (item.scene, item.number)
            if selected or not key in self.batches:
                batch = SelectionBatch(item, selected)
                self.batches[key] = batch
                if not self.scenes.get(item.scene):
                    self.AppendItem(model, model.parent(index), False)

                for line in item.originals:
                    self.originals[line] = SelectionLine(batch.scene, batch.number, line, False)
                for line in item.translated:
                    self.translated[line] = SelectionLine(batch.scene, batch.number, line, False)

    def AddSelectedLines(self, selected_originals : list[SelectionLine], selected_translations : list[SelectionLine]):
        """
        Added selected and/or translated lines to the selection
        """
        for line in selected_originals:
            self.originals[line.number] = line
        for line in selected_translations:
            self.translated[line.number] = line

    def __str__(self):
        if self.selected_originals or self.selected_translated:
            return f"{self.str_lines} in {self.str_batches}"
        if self.selected_scenes:
            return f"{self.str_scenes} with {self.str_lines} in {self.str_batches}"
        elif self.selected_batches:
            return f"{self.str_batches} with {self.str_lines}"
        elif self.original_lines or self.translated_lines:
            return f"{self.str_scenes} with {self.str_lines} in {self.str_batches}"
        elif self.scene_numbers:
            return f"{self.str_scenes}"
        else:
            return "Nothing selected"
        
    def __repr__(self):
        return str(self)

    @property
    def str_scenes(self):
        if self.selected_scenes:
            return self._count(len(self.scene_numbers), "scene", "scenes")
        else:
            return self._count(len(self.selected_scenes), "scene", "scenes")

    @property
    def str_batches(self):
        if self.selected_batches:
           return self._count(len(self.selected_batches), "batch", "batches")
        else:
            return self._count(len(self.batch_numbers), "batch", "batches")

    @property
    def str_originals(self):
        return self._count(len(self.original_lines), "original", "originals")
    
    @property
    def str_selected_originals(self):
        return self._count(len(self.selected_originals), "original", "originals")

    @property
    def str_translated(self):
        return self._count(len(self.translated_lines), "translation", "translations")

    @property
    def str_selected_translated(self):
        return self._count(len(self.selected_translated), "translation", "translations")
    
    @property
    def str_lines(self):
        if self.selected_originals and self.selected_translated:
            return f"{len(self.selected_originals)} original lines and {len(self.selected_translated)} translated lines selected"
        elif self.selected_originals:
            return f"{len(self.selected_originals)} original lines selected"
        elif self.selected_translated:
            return f"{len(self.selected_translated)} translated lines selected"
        elif self.selected_batches:
            selected_batch_numbers = [ batch.number for batch in self.selected_batches ]
            batch_originals = [ x for x in self.originals.values() if x.batch in selected_batch_numbers ]
            batch_translated = [ x for x in self.translated.values() if x.batch in selected_batch_numbers ]
            if batch_originals and batch_translated:
                return f"{len(batch_originals)} original lines and {len(batch_translated)} translated lines"
            elif batch_originals:
                return f"{len(batch_originals)} original lines"
            elif self.translated:
                return f"{len(batch_translated)} translated lines"
        elif self.originals and self.translated:
            return f"{len(self.originals)} original lines and {len(self.translated)} translated lines"
        elif self.originals:
            return f"{len(self.originals)} original lines"
        elif self.translated:
            return f"{len(self.translated)} translated lines"
        else:
            return "nothing selected"

    def _count(self, num, singular, plural):
        if num == 0:
            return f"no {plural}"
        elif num == 1:
            return f"1 {singular}"
        else:
            return f"{num} {plural}"

