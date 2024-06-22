from datetime import timedelta

from PySubtitle.Substitutions import Substitutions
from PySubtitle.TranslationPrompt import TranslationPrompt
from PySubtitle.SubtitleError import SubtitleError
from PySubtitle.Helpers.Subtitles import AddOrUpdateLine, MergeSubtitles
from PySubtitle.SubtitleLine import SubtitleLine
from PySubtitle.Translation import Translation

class SubtitleBatch:
    def __init__(self, dct = None):
        dct = dct or {}
        self.scene = dct.get('scene', None)
        self.number = dct.get('batch') or dct.get('number')
        self.summary = dct.get('summary')
        self.context = dct.get('context', {})
        self.errors = dct.get('errors', [])
        self._originals : list[SubtitleLine] = dct.get('originals', []) or dct.get('subtitles', [])
        self._translated : list[SubtitleLine] = dct.get('translated', [])
        self.translation : Translation = dct.get('translation')
        self.prompt : TranslationPrompt = dct.get('prompt')

    def __str__(self) -> str:
        return f"SubtitleBatch: {str(self.number)} in scene {str(self.scene)} with {self.size} lines"

    def __repr__(self) -> str:
        return str(self)

    @property
    def originals(self) -> list[SubtitleLine]:
        return self._originals

    @property
    def size(self) -> int:
        return len(self._originals)

    @property
    def translated(self) -> list[SubtitleLine]:
        return self._translated

    @property
    def untranslated(self) -> list[SubtitleLine]:
        return [sub for sub in self.originals if not sub.translated]

    @property
    def all_translated(self) -> bool:
        return True if (self.translated and (len(self.translated) == len(self.originals))) else False

    @property
    def any_translated(self) -> bool:
        return len(self.translated or []) > 0

    @property
    def start(self) -> timedelta:
        return self.originals[0].start if self.originals else None

    @property
    def srt_start(self) -> str:
        return self.originals[0].srt_start if self.originals else ""

    @property
    def txt_start(self) -> str:
        return self.originals[0].txt_start if self.originals else ""

    @property
    def end(self) -> timedelta:
        return self.originals[-1].end if self.originals else None

    @property
    def srt_end(self) -> str:
        return self.originals[-1].srt_end if self.originals else ""

    @property
    def txt_end(self) -> str:
        return self.originals[-1].txt_end if self.originals else ""

    @property
    def duration(self) -> timedelta:
        return self.end - self.start if self.start is not None and self.end else timedelta(seconds=0)

    @property
    def first_line_number(self) -> int:
        return self.originals[0].number if self.originals else None

    @property
    def last_line_number(self) -> int:
        return self.originals[-1].number if self.originals else None

    @originals.setter
    def originals(self, value):
        self._originals = [ SubtitleLine(line) for line in value if line.number ] if value else []

    @translated.setter
    def translated(self, value):
        self._translated = [ SubtitleLine(line) for line in value if line.number ] if value else []

    def AddLine(self, line):
        """
        Insert a line into the batch or replace an existing line
        """
        AddOrUpdateLine(self._originals, SubtitleLine(line))

    def AddTranslatedLine(self, line):
       """
       Insert a translated line into the batch or replace an existing translation
       """
       AddOrUpdateLine(self._translated, SubtitleLine(line))

    def HasTranslatedLine(self, line_number):
        if line_number < self.first_line_number or line_number > self.last_line_number:
            return False

        return any(line for line in self._translated if line.number == line_number)

    def GetOriginalLine(self, line_number):
        return next((line for line in self._originals if line.number == line_number), None)

    def GetTranslatedLine(self, line_number):
        return next((line for line in self._translated if line.number == line_number), None)

    def AddContext(self, key, value):
        self.context[key] = value

    def GetContext(self, key):
        return self.context.get(key)

    def SetContext(self, context):
        self.context = context.copy()

    def UpdateContext(self, update) -> bool:
        if not self.context:
            self.context = {}

        updated = False
        for key in update.keys():
            if key == 'summary':
                if update[key] != self.summary:
                    self.summary = update[key]
                    updated = True

            elif update[key] != self.context.get(key):
                self.context[key] = update[key]
                updated = True

        return updated

    def PerformInputSubstitutions(self, substitutions : Substitutions):
        """
        Perform any word/phrase substitutions on source text
        """
        if substitutions and self.originals:
            lines = [item.text for item in self.originals]

            lines, replacements = substitutions.PerformSubstitutionsOnAll(lines)

            if replacements:
                self.AddContext('input_replacements', replacements)
                for item in self.originals:
                    item.text = replacements.get(item.text) or item.text

            return replacements

    def PerformOutputSubstitutions(self, substitutions : Substitutions):
        """
        Perform any word/phrase substitutions on translated text
        """
        if substitutions and self.translated:
            lines = [item.text for item in self.translated]

            _, replacements = substitutions.PerformSubstitutionsOnAll(lines)

            if replacements:
                self.AddContext('output_replacements', replacements)
                for item in self.translated:
                    item.text = replacements.get(item.text) or item.text

            return replacements

    def MergeLines(self, line_numbers : list[int]):
        """
        Merge multiple lines into a single line with the same start/end times
        """
        lines = [line for line in self.originals if line.number in line_numbers]

        if len(lines) < 2:
            raise SubtitleError(f"Cannot merge {len(lines)} lines")

        first_index = self.originals.index(lines[0])
        last_index = self.originals.index(lines[-1])

        merged = MergeSubtitles(lines)
        self.originals = self.originals[:first_index] + [ merged ] + self.originals[last_index + 1:]

        translated_lines = [line for line in self.translated if line.number in line_numbers]

        if translated_lines and len(translated_lines) > 1:
            first_translated_index = self.translated.index(translated_lines[0])
            last_translated_index = self.translated.index(translated_lines[-1])
            merged_translated = MergeSubtitles(translated_lines)
            self.translated = self.translated[:first_translated_index] + [ merged_translated ] + self.translated[last_translated_index + 1:]

            return merged, merged_translated

        return merged, None

    def DeleteLines(self, line_numbers : list[int]) -> bool:
        """
        Delete lines from the batch
        """
        originals = [line for line in self.originals if line.number not in line_numbers]
        translated = [line for line in self.translated if line.number not in line_numbers]

        if len(originals) == len(self.originals) and len(translated) == len(self.translated):
            return [],[]

        deleted_originals = [line for line in self.originals if line.number in line_numbers]
        deleted_translated = [line for line in self.translated if line.number in line_numbers]

        self.originals = originals
        self.translated = translated

        return deleted_originals, deleted_translated

    def InsertOriginalLine(self, line : SubtitleLine):
        """
        Insert a line into the batch
        """
        if not line:
            raise SubtitleError("No line provided to insert")

        if not self.originals:
            self.originals = [line]

        if line.number < self.first_line_number:
            self.originals.insert(0, line)

        elif line.number > self.last_line_number:
            self.originals.append(line)

        else:
            for index, item in enumerate(self.originals):
                if item.number >= line.number:
                    self.originals.insert(index, line)
                    break

    def InsertTranslatedLine(self, line : SubtitleLine):
        """
        Insert a translated line into the batch
        """
        if not line:
            raise SubtitleError("No line provided to insert")

        if not self.translated:
            self.translated = [line]

        if line.number < self.translated[0].number:
            self.translated.insert(0, line)

        elif line.number > self.translated[-1].number:
            self.translated.append(line)

        else:
            for index, item in enumerate(self.translated):
                if item.number >= line.number:
                    self.translated.insert(index, line)
                    break

    def InsertLines(self, originals: list[SubtitleLine], translated: list[SubtitleLine] = None) -> None:
        """
        Insert multiple lines into the batch, with optional translations
        """
        if not originals:
            raise SubtitleError("No original lines provided to insert")

        originals = sorted(originals, key=lambda item: item.number)

        for line in originals:
            self.InsertOriginalLine(line)

        for line in translated or []:
            translated = sorted(translated, key=lambda item: item.number)
            self.InsertTranslatedLine(line)
