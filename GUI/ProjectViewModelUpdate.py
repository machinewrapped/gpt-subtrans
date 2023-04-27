import logging

from GUI.ProjectViewModel import ProjectViewModel


class ModelUpdateSection:
    def __init__(self):
        self.removals = []
        self.additions = {}
        self.updates = {}

    def add(self, key, item):
        self.additions[key] = item

    def remove(self, key):
        self.removals.append(key)

    def update(self, key, item_update):
        self.updates[key] = item_update

    def replace(self, key, item):
        self.removals.append(key)
        self.additions[key] = item

class ModelUpdate:
    def __init__(self):
        self.scenes = ModelUpdateSection()
        self.batches = ModelUpdateSection()
        self.originals = ModelUpdateSection()
        self.translated = ModelUpdateSection()

    def UpdateModel(self, model : ProjectViewModel):
        """
        Incrementally update the viewmodel
        """
        if not model:
            raise Exception("Unable to update ProjectViewModel - no model provided")

        for scene_number in self.scenes.removals:
            model.DeleteScene(scene_number)

        for scene_number, scene in self.scenes.additions.items():
            model.AddScene(scene_number, scene)

        for scene_number, scene_update in self.scenes.updates.items():
            model.UpdateScene(scene_number, scene_update)

        for key in self.batches.removals:
            scene_number, batch_number = key
            model.DeleteBatch(scene_number, batch_number)

        for key, batch_data in self.batches.additions.items():
            scene_number, batch_number = key
            model.AddBatch(scene_number, batch_number, batch_data)

        for key, batch_data in self.batches.updates.items():
            scene_number, batch_number = key
            model.UpdateBatch(scene_number, batch_number, batch_data)

        for key in self.originals.removals:
            scene_number, batch_number, line_number = key
            model.RemoveOriginalLine(scene_number, batch_number, line_number)

        for key in self.originals.additions.items():
            scene_number, batch_number, line_number = key
            model.AddOriginalLine(scene_number, batch_number, line_number)

        for key in self.originals.updates:
            scene_number, batch_number, line_number = key
            model.UpdateOriginalLine(scene_number, batch_number, line_number)

        for key in self.translated.removals:
            scene_number, batch_number, line_number = key
            model.RemoveTranslatedLine(scene_number, batch_number, line_number)

        for key in self.translated.additions.items():
            scene_number, batch_number, line_number = key
            model.AddTranslatedLine(scene_number, batch_number, line_number)

        for key in self.translated.updates:
            scene_number, batch_number, line_number = key
            model.UpdateTranslatedLine(scene_number, batch_number, line_number)
        
        model.layoutChanged.emit()

