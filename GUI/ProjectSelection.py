from PySide6.QtCore import Qt

from GUI.ProjectViewModel import BatchItem, SceneItem, SubtitleItem

class ProjectSelection():
    def __init__(self) -> None:
        self.selection = {}

    @property
    def scene_numbers(self) -> list[int]:
        return [ key for key in self.selection.keys() if isinstance(key, int) ]
    
    @property
    def batch_numbers(self) -> list[(int,int)]:
        batches = []
        for scene_number, scene in self.selection.items():
            batches.extend([ (scene_number, key) for key in scene.keys() if isinstance(key, int)])
        return batches

    @property
    def subtitles(self) -> list[int]:
        subtitles = []
        for scene, batch in self.batch_numbers:
            subtitles.extend(self.selection[scene][batch]['subtitles'].values())
        return subtitles

    @property
    def translated(self) -> list[int]:
        translated = []
        for scene, batch in self.batch_numbers:
            translated.extend( key for key in self.selection[scene][batch]['translated'].values())
        return translated

    @property
    def str_scenes(self):
        return self._count(len(self.scene_numbers), "scene", "scenes")

    @property
    def str_batches(self):
        return self._count(len(self.batch_numbers), "batch", "batches")

    @property
    def str_subtitles(self):
        return self._count(len(self.subtitles), "subtitle", "subtitles")

    @property
    def str_translated(self):
        return self._count(len(self.translated), "translation", "translations")

    def Any(self):
        return self.scene_numbers or self.batch_numbers or self.subtitles or self.translated
    
    def GetSelectionMap(self):
        selection = {}
        for scene_number, scene in self.selection.items():
            selection[scene_number] = { 'selected' : scene.get('selected', False) }

            batch_numbers = [ key for key in scene.keys() if isinstance(key, int)]
            for batch_number in batch_numbers:
                batch = self.selection[scene_number][batch_number]
                selection[scene_number][batch_number] = { 
                    'selected' : True,
                    'subtitles' : batch['subtitles'].keys(),
                    'translated' : batch['translated'].keys() 
                    }

        return selection

    def AppendItem(self, model, index, selected : bool = True):
        """
        Accumulated selected batches, scenes and subtitles
        """
        item = model.data(index, role=Qt.ItemDataRole.UserRole)

        if isinstance(item, SceneItem):
            self.selection[item.number] = { 'selected' : selected, 'item': item }

            for child_index in [ model.index(i, 0, index) for i in range(model.rowCount(index))]:
                self.AppendItem(model, child_index, False)

        elif isinstance(item, BatchItem):
            self.selection[item.scene] = self.selection.get(item.scene) or { }
            self.selection[item.scene][item.number] = { 
                'selected' : selected,
                'item' : item,
                'subtitles' : { line['index'] : line for line in item.subtitles },
                'translated' : { line['index'] : line for line in item.translated },
                }

    def __str__(self):
        if self.scene_numbers:
            return f"{self.str_scenes} with {self.str_subtitles} and {self.str_translated} in {self.str_batches}"
        elif self.batch_numbers:
            return f"{self.str_subtitles} and {self.str_translated} in {self.str_batches}"
        elif self.translated:
            return f"{self.str_subtitles} and {self.str_translated}"
        elif self.subtitles:
            return f"{self.str_subtitles}"
        else:
            return "Nothing selected"

    def _count(self, num, singular, plural):
        if num == 0:
            return f"No {plural}"
        elif num == 1:
            return f"1 {singular}"
        else:
            return f"{num} {plural}"

