import logging

from PySide6.QtCore import Qt

from GUI.GuiHelpers import DescribeLineCount
from GUI.ViewModel.LineItem import LineItem
from GUI.ViewModel.ViewModelItem import ViewModelItem
from GUI.ViewModel.ViewModelError import ViewModelError

from PySubtitle.Helpers import FormatMessages, UpdateFields
from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.Translation import Translation
from PySubtitle.TranslationPrompt import TranslationPrompt

class BatchItem(ViewModelItem):
    """ Represents a subtitle batch in the view model"""
    def __init__(self, scene_number : int, batch : SubtitleBatch, debug_view : bool = False):
        super(BatchItem, self).__init__(f"Scene {scene_number}, batch {batch.number}")
        self.scene = scene_number
        self.number = batch.number
        self.debug_view = debug_view
        self.lines = {}
        self.batch_model = {
            'start': batch.txt_start,
            'end': batch.srt_end,
            'summary': batch.summary,
            'errors': self._get_errors(batch.errors),
            'translated': batch.translation is not None
        }

        # cache on demand
        self._first_line_num = None
        self._last_line_num = None

        if batch.translation and isinstance(batch.translation, Translation):
            self.batch_model.update({
                'response': batch.translation.FormatResponse(),
                'context': batch.context
            })

        if batch.prompt:
            self.batch_model.update({
                'prompt': FormatPrompt(batch.prompt)
            })

            if self.debug_view:
                self.batch_model.update({
                    'messages': FormatMessages(batch.prompt.messages)
                })

        self.setData(self.batch_model, Qt.ItemDataRole.UserRole)

    @property
    def line_count(self) -> int:
        return len(self.lines)

    @property
    def translated_count(self) -> int:
        return len([line for line in self.lines.values() if line.translation is not None])

    @property
    def all_translated(self) -> bool:
        return self.translated_count == self.line_count

    @property
    def translated(self) -> bool:
        return self.batch_model.get('translated')

    @property
    def start(self) -> str:
        return self.batch_model['start']

    @property
    def end(self) -> str:
        return self.batch_model['end']

    @property
    def context(self) -> str:
        return self.batch_model.get('context')

    @property
    def summary(self) -> str:
        return self.batch_model.get('summary')

    @property
    def response(self) -> str:
        return self.batch_model.get('response')

    @property
    def prompt(self) -> str:
        return self.batch_model.get('prompt')

    @property
    def first_line_number(self) -> int:
        if not self._first_line_num:
            self._update_first_and_last()
        return self._first_line_num

    @property
    def last_line_number(self) -> int:
        if not self._last_line_num:
            self._update_first_and_last()
        return self._last_line_num

    @property
    def has_errors(self) -> bool:
        return True if self.batch_model.get('errors') else False

    def Update(self, update : dict):
        """
        Update the batch model properties
        """
        if not isinstance(update, dict):
            raise ViewModelError(f"Expected a dictionary, got a {type(update).__name__}")

        UpdateFields(self.batch_model, update, ['number', 'summary', 'context', 'start', 'end'])

        if 'errors' in update.keys():
            self.batch_model['errors'] = self._get_errors(update['errors'])

        if 'translation' in update.keys():
            translation = update['translation']
            if isinstance(translation, Translation):
                self.batch_model.update({
                    'response': translation.FormatResponse()
                })

        if 'prompt' in update.keys():
            prompt = update['prompt']
            if isinstance(prompt, TranslationPrompt):
                self.batch_model.update({
                    'prompt': FormatPrompt(prompt)
                })
                if self.debug_view:
                    self.batch_model.update({
                        'messages': FormatMessages(prompt.messages)
                    })

        self.setData(self.batch_model, Qt.ItemDataRole.UserRole)

    def AddLineItem(self, line_number : int, model : dict):
        """
        Add an original line item to the batch
        """
        line_item : LineItem = LineItem(line_number, model)
        last_line_item = self.child(self.rowCount() - 1, 0) if self.rowCount() > 0 else None

        if not last_line_item or line_number > last_line_item.number:
            self.appendRow(line_item)
            self.lines[line_number] = line_item
        else:
            for row in range(self.rowCount()):
                row_item : LineItem = self.child(row, 0)
                if not row_item.number:
                    raise ViewModelError(f"Line item {row} has no line number")

                if row_item.number < line_number:
                    continue

                # Insert the new line at the first opportunity
                if line_item:
                    self.insertRow(row, line_item)
                    self.lines[line_number] = line_item
                    line_item = None
                    if row_item.number > line_number:
                        # No need to adjust the following line numbers
                        break

                row_item.number = row_item.number + 1
                self.lines[row_item.number] = row_item

        self._invalidate_first_and_last()

    def AddTranslation(self, line_number : int, text : str):
        """
        Add a translation to the line item
        """
        if line_number in self.lines.keys():
            line_item : LineItem = self.lines[line_number]
            line_item.Update({ 'translation' : text })
        else:
            logging.warning(f"Original line {line_number} not found in batch {self.number}")

    def GetContent(self):
        """
        Return a dictionary of interesting batch data for UI display
        """
        body = "\n".join(e for e in self.batch_model.get('errors')) if self.has_errors \
            else self.summary if self.summary \
            else "\n".join([
                "1 line" if self.line_count == 1 else f"{self.line_count} lines",
                f"{self.translated_count} translated" if self.translated_count > 0 else ""
            ])

        return {
            'heading': f"Batch {self.number}",
            'subheading': f"Lines {self.first_line_number}-{self.last_line_number} ({self.start} -> {self.end})",
            'body': body,
            'footer': DescribeLineCount(self.line_count, self.translated_count),
            'properties': {
                'all_translated' : self.all_translated,
                'errors' : self.has_errors
            }
        }

    def _update_first_and_last(self):
        line_numbers = [ num for num in self.lines.keys() if num ] if self.lines else None
        self._first_line_num = min(line_numbers) if line_numbers else None
        self._last_line_num = max(line_numbers) if line_numbers else None

    def _invalidate_first_and_last(self):
        self._first_line_num = None
        self._last_line_num = None

    def _get_errors(self, errors) -> list[str]:
        if errors:
            if all(isinstance(e, Exception) for e in errors):
                return [ str(e) for e in errors ]
            if all(isinstance(e, dict) for e in errors):
                return [ e.get('problem') for e in errors if e.get('problem') ]
        return []

    def __str__(self) -> str:
        content = self.GetContent()
        return f"{content['heading']}\n{content['subheading']}\n{content['body']}"


def FormatPrompt(prompt : TranslationPrompt):
    """
    Format a prompt for display to the user
    """
    if prompt.batch_prompt:
        return prompt.batch_prompt
    else:
        lines = []

        if prompt.user_prompt:
            lines.append(f"User Prompt:\n {prompt.user_prompt}")

        return "\n".join(lines)