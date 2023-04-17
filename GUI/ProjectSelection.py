from PySide6.QtCore import Qt

from GUI.ProjectViewModel import BatchItem, SceneItem

class SelectionScene:
    def __init__(self, scene : SceneItem, selected : bool = True) -> None:
        self.number = scene.number
        self.selected = selected
        self.batches = {}

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
        self.originals = {}
        self.translated = {}

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

    @property
    def scene_numbers(self) -> list[int]:
        return sorted([ key for key in self.scenes.keys() ])
    
    @property
    def selected_scenes(self) -> list[SelectionScene]:
        return [ selection.number for selection in self.scenes.values() if selection.selected]
    
    @property
    def batch_numbers(self) -> list[(int,int)]:
        batches = []
        for scene in self.scenes.values():
            batches.extend([ (scene.number, key) for key in scene.batches.keys() ])
        return sorted(batches)

    @property
    def selected_batches(self) -> list[SelectionBatch]:
        batches = []
        for scene in self.scenes.values():
            batches.extend([ batch for batch in scene.batches.values() if batch.selected])
        return batches

    @property
    def original_lines(self) -> list[SelectionLine]:
        originals = []
        for scene, batch in self.batch_numbers:
            originals.extend(self.scenes[scene][batch].originals.values())
        return originals
    
    @property 
    def selected_originals(self) -> list[SelectionLine]:
        return [line for line in self.original_lines if line.selected ]

    @property
    def translated_lines(self) -> list[SelectionLine]:
        translated = []
        for scene, batch in self.batch_numbers:
            translated.extend(self.scenes[scene][batch].translated.values())
        return translated

    @property 
    def selected_translations(self) -> list[SelectionLine]:
        return [line for line in self.translated_lines if line.selected ]

    def Any(self) -> bool:
        return self.scene_numbers or self.batch_numbers or self.original_lines or self.translated_lines
    
    def AnyScenes(self) -> bool:
        return self.selected_scenes and True
    
    def OnlyScenes(self) -> bool:
        return self.selected_scenes and not self.selected_batches
    
    def AnyBatches(self) -> bool:
        return self.selected_batches and True

    def OnlyBatches(self) -> bool:
        return self.selected_batches and not self.selected_scenes

    def AnyLines(self) -> bool:
        return self.selected_originals or self.selected_translations
    
    def MatchingLines(self) -> bool:
        return self.selected_originals == self.selected_translations

    def MultipleSelected(self) -> bool:
        return len(self.selected_scenes) > 1 or len(self.selected_batches) > 1 or len(self.selected_originals) > 1 or len(self.selected_translations) > 1

    def SelectionIsSequential(self) -> bool:
        if self.selected_scenes:
            scene_numbers = self.scene_numbers
            if scene_numbers != list(range(self.scene_numbers[0], self.scene_numbers[0] + len(self.scene_numbers))):
                return False
            
        batches = self.selected_batches
        if batches:
            if not all(batch.scene == batches[0].scene for batch in batches):
                return False

            batch_numbers = [ batch.number for batch in batches ]
            if batch_numbers != list(range(batch_numbers[0], batch_numbers[0] + len(batches))):
                return False
            
        originals = self.selected_originals
        if originals:
            if not all(line.scene == line[0].scene and line.batch == line[0].batch for line in originals):
                return False
            
            line_numbers = [ line.number for line in originals ]
            if line_numbers != list(range(line_numbers[0], line_numbers[0] + len(line_numbers))):
                return False
            
        translated = self.selected_translations
        if translated:
            if not all(line.scene == line[0].scene and line.batch == line[0].batch for line in translated):
                return False
            
            line_numbers = [ line.number for line in translated ]
            if line_numbers != list(range(line_numbers[0], line_numbers[0] + len(line_numbers))):
                return False

        
        return True

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
            batch.originals = { line : SelectionLine(line, batch.number, batch.scene, False) for line in item.originals.keys() }
            batch.translated = { line : SelectionLine(line, batch.number, batch.scene, False) for line in item.translated.keys() }

            if not self.scenes.get(item.scene):
                self.AppendItem(model, model.parent(index), False)

            self.scenes[item.scene][item.number] = batch

    def AppendLines(self, selected_originals : list[SelectionLine], selected_translations : list[SelectionLine]):
        # Assume the scenes and batches that contains the lines have already been added
        for line in selected_originals:
            batch : SelectionBatch = self.scenes[line.scene][line.batch]
            batch.originals[line.number] = line

        for line in selected_translations:
            batch : SelectionBatch = self.scenes[line.scene][line.batch]
            batch.translated[line.number] = line


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
            return f"No {plural}"
        elif num == 1:
            return f"1 {singular}"
        else:
            return f"{num} {plural}"

