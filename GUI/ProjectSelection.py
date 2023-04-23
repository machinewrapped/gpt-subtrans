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
        # 90% sure it would be better to store the selection as flat lists & construct the hierarchy on demand 
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
        return sorted([ number for number in self.originals.keys() ])
    
    @property 
    def selected_originals(self) -> list[SelectionLine]:
        return [line for line in self.originals.values() if line.selected ]

    @property
    def translated_lines(self) -> list[SelectionLine]:
        return sorted([ number for number in self.translated.keys() ])

    @property 
    def selected_translations(self) -> list[SelectionLine]:
        return [line for line in self.translated.values() if line.selected ]

    def Any(self) -> bool:
        return self.scene_numbers or self.batch_numbers or self.original_lines or self.translated_lines
    
    def AnyScenes(self) -> bool:
        return self.selected_scenes and True
    
    def OnlyScenes(self) -> bool:
        return self.selected_scenes and not (self.selected_batches or self.selected_originals or self.selected_translations)
    
    def AnyBatches(self) -> bool:
        return self.selected_batches and True

    def OnlyBatches(self) -> bool:
        return self.selected_batches  and not (self.selected_scenes or self.selected_originals or self.selected_translations)

    def AnyLines(self) -> bool:
        return self.selected_originals or self.selected_translations
    
    def AllLinesInSameBatch(self) -> bool:
        originals = self.selected_originals
        translated = self.selected_translations
        return all(line.batch == originals[0].batch for line in originals) and all(line.batch == translated[0].batch for line in translated)

    def MatchingLines(self) -> bool:
        return self.selected_originals == self.selected_translations

    def MultipleSelected(self) -> bool:
        return len(self.selected_scenes) > 1 or len(self.selected_batches) > 1 or len(self.selected_originals) > 1 or len(self.selected_translations) > 1

    def IsSequential(self) -> bool:
        scene_numbers = sorted(scene.number for scene in self.selected_scenes)
        if scene_numbers and scene_numbers != list(range(scene_numbers[0], scene_numbers[0] + len(scene_numbers))):
            return False

        if not all(batch.scene == self.selected_batches[0].scene for batch in self.selected_batches):
            return False

        batch_numbers = sorted(batch.number for batch in self.selected_batches)
        if batch_numbers and batch_numbers != list(range(batch_numbers[0], batch_numbers[0] + len(batch_numbers))):
            return False

        if not all(batch.scene == batch_numbers[0].scene for batch in self.selected_batches):
            return False

        line_numbers = sorted(line.number for line in self.selected_originals)
        if line_numbers and line_numbers != list(range(line_numbers[0], line_numbers[0] + len(line_numbers))):
            return False

        line_numbers = sorted(line.number for line in self.selected_translations)
        if line_numbers and line_numbers != list(range(line_numbers[0], line_numbers[0] + len(line_numbers))):
            return False

        return True
    
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

        for line in self.selected_translations:
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
            self.scenes[item.number] = SelectionScene(item, selected)

            children = [ model.index(i, 0, index) for i in range(model.rowCount(index))]
            for child_index in children:
                self.AppendItem(model, child_index, False)

        elif isinstance(item, BatchItem):
            batch = SelectionBatch(item, selected)
            self.batches[item.number] = batch
            if not self.scenes.get(item.scene):
                self.AppendItem(model, model.parent(index), False)

            for line in item.originals:
                self.originals[line] = SelectionLine(batch.scene, batch.number, line, False)
            for line in item.translated:
                self.translated[line] = SelectionLine(batch.scene, batch.number, line, False)

    def AddSelectedLines(self, selected_originals : list[SelectionLine], selected_translations : list[SelectionLine]):
        for line in selected_originals:
            self.originals[line.number] = line
        for line in selected_translations:
            self.translations[line.number] = line

    def __str__(self):
        if self.scene_numbers:
            return f"{self.str_scenes} with {self.str_originals} and {self.str_translated} in {self.str_batches}"
        elif self.batch_numbers:
            return f"{self.str_originals} and {self.str_translated} in {self.str_batches}"
        elif self.translated_lines:
            return f"{self.str_originals} and {self.str_translated}"
        elif self.original_lines:
            return f"{self.str_originals}"
        else:
            return "Nothing selected"
        
    def __repr__(self):
        return str(self)

    @property
    def str_scenes(self):
        return self._count(len(self.scene_numbers), "scene", "scenes")

    @property
    def str_batches(self):
        return self._count(len(self.batch_numbers), "batch", "batches")

    @property
    def str_originals(self):
        return self._count(len(self.original_lines), "original", "originals")

    @property
    def str_translated(self):
        return self._count(len(self.translated_lines), "translation", "translations")

    def _count(self, num, singular, plural):
        if num == 0:
            return f"no {plural}"
        elif num == 1:
            return f"1 {singular}"
        else:
            return f"{num} {plural}"

