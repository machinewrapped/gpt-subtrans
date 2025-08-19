from GUI.ViewModel.ViewModelUpdateSection import ModelUpdateSection
from GUI.ViewModel.ViewModel import ProjectViewModel

class ModelUpdate:
    def __init__(self):
        self.scenes : ModelUpdateSection = ModelUpdateSection()
        self.batches : ModelUpdateSection = ModelUpdateSection()
        self.lines : ModelUpdateSection = ModelUpdateSection()

    def HasUpdate(self) -> bool:
        """ Returns True if there are any updates """
        return self.scenes.has_updates or self.batches.has_updates or self.lines.has_updates

    def ApplyToViewModel(self, viewmodel : ProjectViewModel):
        """ Apply the updates to the viewmodel """
        for scene_number, scene in self.scenes.replacements.items():
            viewmodel.ReplaceScene(scene)

        for scene_number, scene_update in self.scenes.updates.items():
            viewmodel.UpdateScene(scene_number, scene_update)

        for scene_number in reversed(self.scenes.removals):
            viewmodel.RemoveScene(scene_number)

        for scene_number, scene in self.scenes.additions.items():
            viewmodel.AddScene(scene)

        for key, batch in self.batches.replacements.items():
            scene_number, batch_number = key
            viewmodel.ReplaceBatch(batch)

        for key, batch_update in self.batches.updates.items():
            scene_number, batch_number = key
            viewmodel.UpdateBatch(scene_number, batch_number, batch_update)

        for key in reversed(self.batches.removals):
            scene_number, batch_number = key
            viewmodel.RemoveBatch(scene_number, batch_number)

        for key, batch in self.batches.additions.items():
            scene_number, batch_number = key
            viewmodel.AddBatch(batch)

        if self.lines.updates:
            batched_line_updates = self.GetUpdatedLinesInBatches()
            for key, line_updates in batched_line_updates.items():
                scene_number, batch_number = key
                viewmodel.UpdateLines(scene_number, batch_number, line_updates)

        if self.lines.removals:
            batched_line_removals = self.GetRemovedLinesInBatches()
            for key, line_numbers in batched_line_removals.items():
                scene_number, batch_number = key
                viewmodel.RemoveLines(scene_number, batch_number, line_numbers)

        for key, line in self.lines.additions.items():
            scene_number, batch_number, line_number = key
            if line_number != line.number:
                raise ValueError(f"Line number mismatch: {line_number} != {line.number}")
            viewmodel.AddLine(scene_number, batch_number, line)

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
        for line_key, line in self.lines.updates.items():
            scene_number, batch_number, line_number = line_key
            batch_key = (scene_number, batch_number)
            if batch_key in batches:
                batches[batch_key][line_number] = line
            else:
                batches[batch_key] = { line_number: line }

        return batches