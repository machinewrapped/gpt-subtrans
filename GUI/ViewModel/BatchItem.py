from GUI.GuiHelpers import DescribeLineCount
from GUI.ViewModel.LineItem import LineItem
from GUI.ProjectViewModel import ViewModelError, ViewModelItem
from PySubtitle.Helpers import FormatMessages, UpdateFields
from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.Translation import Translation
from PySubtitle.TranslationPrompt import FormatPrompt, TranslationPrompt


from PySide6.QtCore import Qt


import logging


class BatchItem(ViewModelItem):
    def __init__(self, scene_number, batch : SubtitleBatch, debug_view = False):
        super(BatchItem, self).__init__(f"Scene {scene_number}, batch {batch.number}")
        self.scene = scene_number
        self.number = batch.number
        self.debug_view = debug_view
        self.lines = {}
        self.translated = {}
        self.batch_model = {
            'start': batch.srt_start,
            'end': batch.srt_end,
            'summary': batch.summary,
            'errors': self._get_errors(batch.errors)
        }

        # cache on demand
        self._first_line_num = None
        self._last_line_num = None

        if batch.translation:
            self.batch_model.update({
                'response': batch.translation.text,
                'context': batch.context,
            })

        if batch.translation:
            self.batch_model.update({
                'response': batch.translation.FormatResponse()
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

    def AddLineItem(self, line_number : int, model : dict):
        line_item : LineItem = LineItem(line_number, model)
        self.appendRow(line_item)

        self.lines[line_number] = line_item

        self._invalidate_first_and_last()

    def AddTranslation(self, line_number : int, text : str):
        if line_number in self.lines.keys():
            line_item : LineItem = self.lines[line_number]
            line_item.Update({ 'translation': text })
        else:
            logging.warning(f"Original line {line_number} not found in batch {self.number}")

    @property
    def line_count(self):
        return len(self.lines)

    @property
    def translated_count(self):
        return len([line for line in self.lines.values() if line.translation])

    @property
    def all_translated(self):
        return self.translated_count == self.line_count

    @property
    def start(self):
        return self.batch_model['start']

    @property
    def end(self):
        return self.batch_model['end']

    @property
    def context(self):
        return self.batch_model.get('context')

    @property
    def summary(self):
        return self.batch_model.get('summary')

    @property
    def response(self):
        return self.batch_model.get('response')

    @property
    def prompt(self):
        return self.batch_model.get('prompt')

    @property
    def first_line_number(self):
        if not self._first_line_num:
            self._update_first_and_last()
        return self._first_line_num

    @property
    def last_line_number(self):
        if not self._last_line_num:
            self._update_first_and_last()
        return self._last_line_num

    @property
    def has_errors(self):
        return True if self.batch_model.get('errors') else False

    def Update(self, update : dict):
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

    def GetContent(self):
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
        self._last_line_num = max(line_numbers)

    def _invalidate_first_and_last(self):
        self._first_line_num = None
        self._last_line_num = None

    def _get_errors(self, errors):
        if errors:
            if all(isinstance(e, Exception) for e in errors):
                return [ str(e) for e in errors ]
            if all(isinstance(e, dict) for e in errors):
                return [ e.get('problem') for e in errors if e.get('problem') ]
        return []

    def __str__(self) -> str:
        content = self.GetContent()
        return f"{content['heading']}\n{content['subheading']}\n{content['body']}"