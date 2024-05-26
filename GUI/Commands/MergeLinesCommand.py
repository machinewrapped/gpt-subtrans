from GUI.Command import Command, CommandError, UndoError
from GUI.ProjectDataModel import ProjectDataModel
from GUI.ProjectSelection import ProjectSelection
from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.SubtitleProject import SubtitleProject

import logging

class MergeLinesCommand(Command):
    """
    Merge one or several lines together
    """
    def __init__(self, selection : ProjectSelection, datamodel: ProjectDataModel = None):
        super().__init__(datamodel)
        self.selection = selection
        self.undo_data = []
        self.can_undo = True

    def execute(self):
        subtitles : SubtitleFile = self.datamodel.project.subtitles

        if not subtitles:
            raise CommandError("No subtitles", command=self)

        line_numbers = sorted([line.number for line in self.selection.selected_lines])

        batches = subtitles.GetBatchesContainingLines(line_numbers)

        if not batches:
            raise CommandError("No batches found for lines to merge", command=self)

        model_update = self.AddModelUpdate()
        for batch in batches:
            batch_lines = [number for number in line_numbers if number >= batch.first_line_number and number <= batch.last_line_number]
            originals = [batch.GetOriginalLine(line_number) for line_number in batch_lines]
            translated = [batch.GetTranslatedLine(line_number) for line_number in batch_lines]

            logging.info(f"Merging lines {str([line.number for line in originals])} in batch {str((batch.scene, batch.number))}")

            if any([line is None for line in originals]):
                raise CommandError("Cannot merge lines, some lines are missing", command=self)

            translated = [line for line in translated if line is not None]

            self.undo_data.append((batch.scene, batch.number, originals, translated))

            merged_line, merged_translated = subtitles.MergeLinesInBatch(batch.scene, batch.number, batch_lines)

            if not merged_line:
                raise CommandError("Failed to merge lines", command=self)

            line_update = {
                'start': merged_line.start,
                'end': merged_line.end,
                'text': merged_line.text,
                }

            if merged_translated:
                line_update['translation'] = merged_translated.text

            model_update.lines.update((batch.scene, batch.number, merged_line.number), line_update)

            for line in batch_lines[1:]:
                model_update.lines.remove((batch.scene, batch.number, line))

        return True

    def undo(self):
        if not self.undo_data:
            raise UndoError("Cannot undo merge, undo data was not saved", command=self)

        subtitles : SubtitleFile = self.datamodel.project.subtitles

        updates = {}
        for scene_number, batch_number, original_lines, translated_lines in self.undo_data:
            batch : SubtitleBatch = subtitles.GetBatch(scene_number, batch_number)
            for line in original_lines:
                batch.AddLine(line)
                updates[(scene_number, batch_number, line.number)] = { 'start': line.start, 'end': line.end, 'text': line.text }

            for line in translated_lines:
                batch.AddTranslatedLine(line)
                updates[(scene_number, batch_number, line.number)]['translation'] = line.text

        model_update = self.AddModelUpdate()
        model_update.lines.updates = updates
