from GUI.ProjectDataModel import ProjectDataModel
from GUI.ProjectViewModel import ProjectViewModel

class ModelUpdateSection:
    def __init__(self):
        self.updates = {}
        self.replacements = {}
        self.removals = []
        self.additions = {}

    def update(self, key, item_update):
        self.updates[key] = item_update

    def replace(self, key, item):
        self.replacements[key] = item

    def add(self, key, item):
        self.additions[key] = item

    def remove(self, key):
        self.removals.append(key)

    def HasUpdate(self) -> bool:
        return self.updates or self.replacements or self.additions or self.removals

class ModelUpdate:
    def __init__(self):
        self.rebuild = False
        self.scenes = ModelUpdateSection()
        self.batches = ModelUpdateSection()
        self.originals = ModelUpdateSection()
        self.translated = ModelUpdateSection()

    def HasUpdate(self) -> bool:
        return self.scenes.HasUpdate() or self.batches.HasUpdate() or self.originals.HasUpdate() or self.translated.HasUpdate()

    def UpdateModel(self, datamodel: ProjectDataModel):
        """
        Patch the viewmodel
        """
        if not datamodel or not isinstance(datamodel, ProjectDataModel):
            raise Exception("Invalid datamodel")
        
        if self.rebuild:
            datamodel.CreateViewModel()
            return
                
        with datamodel.GetLock():
            viewmodel : ProjectViewModel = datamodel.viewmodel
            viewmodel.beginResetModel()
            viewmodel.blockSignals(True)

            for scene_number, scene_update in self.scenes.updates.items():
                viewmodel.UpdateScene(scene_number, scene_update)

            for key, batch_update in self.batches.updates.items():
                scene_number, batch_number = key
                viewmodel.UpdateBatch(scene_number, batch_number, batch_update)

            #TODO: Use UpdateOriginalLines
            for key, line_update in self.originals.updates.items():
                scene_number, batch_number, line_number = key
                viewmodel.UpdateOriginalLine(scene_number, batch_number, line_number, line_update)

            #TODO: Use UpdateTranslatedLines
            for key, line_update in self.translated.updates.items():
                scene_number, batch_number, line_number = key
                viewmodel.UpdateTranslatedLine(scene_number, batch_number, line_number, line_update)

            for scene_number, scene in self.scenes.replacements.items():
                viewmodel.ReplaceScene(scene)

            for key, batch in self.batches.replacements.items():
                scene_number, batch_number = key
                viewmodel.ReplaceBatch(batch)

            for scene_number in reversed(self.scenes.removals):
                viewmodel.RemoveScene(scene_number)

            for key in reversed(self.batches.removals):
                scene_number, batch_number = key
                viewmodel.RemoveBatch(scene_number, batch_number)

            for key in reversed(self.originals.removals):
                scene_number, batch_number, line_number = key
                viewmodel.RemoveOriginalLine(scene_number, batch_number, line_number)

            for key in reversed(self.translated.removals):
                scene_number, batch_number, line_number = key
                viewmodel.RemoveTranslatedLine(scene_number, batch_number, line_number)

            for scene_number, scene in self.scenes.additions.items():
                viewmodel.AddScene(scene)

            for key, batch in self.batches.additions.items():
                scene_number, batch_number = key
                viewmodel.AddBatch(batch)

            for key, line in self.originals.additions.items():
                scene_number, batch_number, line_number = key
                viewmodel.AddOriginalLine(scene_number, batch_number, line_number, line)

            for key, line in self.translated.additions.items():
                scene_number, batch_number, line_number = key
                viewmodel.AddTranslatedLine(scene_number, batch_number, line_number, line)

            # Rebuild the model dictionaries
            viewmodel.Remap()
            viewmodel.blockSignals(False)
            viewmodel.endResetModel()
        
        viewmodel.layoutChanged.emit()

