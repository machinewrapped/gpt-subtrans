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
    
    @property
    def size_changed(self) -> bool:
        return self.removals or self.additions

class ModelUpdate:
    def __init__(self):
        self.rebuild = False
        self.scenes = ModelUpdateSection()
        self.batches = ModelUpdateSection()
        self.lines = ModelUpdateSection()

    def HasUpdate(self) -> bool:
        """ Returns True if there are any updates """
        return self.scenes.HasUpdate() or self.batches.HasUpdate() or self.lines.HasUpdate()

    def ApplyToViewModel(self, viewmodel : ProjectViewModel):
        """ Apply the updates to the viewmodel """
        for scene_number, scene_update in self.scenes.updates.items():
            viewmodel.UpdateScene(scene_number, scene_update)

        for key, batch_update in self.batches.updates.items():
            scene_number, batch_number = key
            viewmodel.UpdateBatch(scene_number, batch_number, batch_update)

        if self.lines.updates:
            batched_line_updates = self.GetUpdatedLinesInBatches()
            for key, line_updates in batched_line_updates.items():
                scene_number, batch_number = key
                viewmodel.UpdateLines(scene_number, batch_number, line_updates)

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

        if self.lines.removals:
            batched_line_removals = self.GetRemovedLinesInBatches()
            for key, line_numbers in batched_line_removals.items():
                scene_number, batch_number = key
                viewmodel.RemoveLines(scene_number, batch_number, line_numbers)

        for scene_number, scene in self.scenes.additions.items():
            viewmodel.AddScene(scene)

        for key, batch in self.batches.additions.items():
            scene_number, batch_number = key
            viewmodel.AddBatch(batch)

        for key, line in self.lines.additions.items():
            scene_number, batch_number, line_number = key
            viewmodel.AddLine(scene_number, batch_number, line_number, line)

    def GetRemovedLinesInBatches(self):
        """ 
        Returns a dictionary of removed lines in batches. 
        
        returns:
            dict: The key is a tuple of (scene_number, batch_number) and the value is a list of line numbers.
        """
        batches = {}
        for scene_number, batch_number, line_number in self.lines.removals:
            key = (scene_number, batch_number)
            if key not in batches:
                batches[key] = [ line_number ]
            else:
                batches[key].append(line_number)

        return batches

    def GetUpdatedLinesInBatches(self):
        """
        Returns a dictionary of updated lines in batches. 
        
        returns:
            dict: The key is a tuple of (scene_number, batch_number) and the value is a dictionary of line numbers and their updates.
        """
        batches = {}
        for scene_number, batch_number, line in self.lines.updates:
            key = (scene_number, batch_number)
            if key not in batches:
                batches[key] = [ line ]
            else:
                batches[key].append(line)

        return batches