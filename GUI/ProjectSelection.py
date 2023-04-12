from PySide6.QtCore import Qt

from GUI.ProjectViewModel import BatchItem, SceneItem

class ProjectSelection():
    def __init__(self) -> None:
        self.selection = {}

        self.scenes = []
        self.batches = []
        self.subtitles = []
        self.translated = []

    @property
    def str_scenes(self):
        return self._count(len(self.scenes), "scene", "scenes")

    @property
    def str_batches(self):
        return self._count(len(self.batches), "batch", "batches")

    @property
    def str_subtitles(self):
        return self._count(len(self.subtitles), "subtitle", "subtitles")

    @property
    def str_translated(self):
        return self._count(len(self.translated), "translation", "translations")

    def Any(self):
        return self.scenes or self.batches or self.subtitles or self.translated
    
    def GetSelection(self):
        selection = {}
        for scene_number, scene in self.selection.items():
            selection[scene_number] = { 'selected' : scene.get('selected', False) }

            for key in scene.keys():
                if isinstance(key, int):
                    selection[scene_number][key] = { 'selected' : True }

                    #TODO add individual lines to batches

        return selection

    def AppendItem(self, model, index):
        """
        Accumulated selected batches, scenes and subtitles
        """
        item = model.data(index, role=Qt.ItemDataRole.UserRole)
        if isinstance(item, SceneItem):
            self.scenes.append(item)

            self.selection[item.number] = { 'selected' : True, 'item' : item }
            children = [ model.index(i, 0, index) for i in range(model.rowCount(index))]
            for child_index in children:
                child_item = model.data(child_index, role=Qt.ItemDataRole.UserRole)
                self.batches.append(child_item)
                self.subtitles.extend(child_item.subtitles)
                self.translated.extend(child_item.translated)

        elif isinstance(item, BatchItem):
            self.batches.append(item)
            self.subtitles.extend(item.subtitles)
            self.translated.extend(item.translated)

            scene = self.selection.get(item.scene) or { }
            scene[item.number] = { 'selected' : True, 'item' : item, 'subtitles' : item.subtitles, 'translated' : item.translated }
            self.selection[item.scene] = scene

    def __str__(self):
        if self.scenes:
            return f"{self.str_scenes} with {self.str_subtitles} and {self.str_translated} in {self.str_batches}"
        elif self.batches:
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

