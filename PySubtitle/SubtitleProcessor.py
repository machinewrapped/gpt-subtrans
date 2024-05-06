import logging
import regex
from datetime import timedelta

from PySubtitle.Helpers.Subtitles import FindSplitPoint, GetProportionalDuration
from PySubtitle.Helpers.Text import (
    dialog_marker,
    split_sequences,
    break_sequences,
    BreakLongLine,
    BreakDialogOnOneLine,
    CompileDialogSplitPattern,
    CompileFillerWordsPattern,
    ConvertWhitespaceBlocksToNewlines,
    NormaliseDialogTags,
    RemoveFillerWords
)
from PySubtitle.Options import Options
from PySubtitle.SubtitleLine import SubtitleLine

class SubtitleProcessor:
    """
    Helper class to pre-process subtitles to make them suitable for translation.

    Will split long lines, add line breaks and remove empty lines.
    """
    def __init__(self, settings : Options | dict):
        self.dialog_marker = dialog_marker
        self.split_sequences = split_sequences
        self.break_sequences = break_sequences
        self._compiled_split_sequences = None
        self._compiled_break_sequences = None
        self.forbidden_start_end_pairs = [
            ("<", ">"),
            ("[", "]"),
            ("(", ")"),
            ('"', '"'),
            ("“", "”"),
            ("‘", "’"),
        ]

        self.max_line_duration = timedelta(seconds = settings.get('max_line_duration', 0.0))
        self.min_line_duration = timedelta(seconds = settings.get('min_line_duration', 0.0))
        self.min_gap = timedelta(seconds=settings.get('min_gap', 0.05))
        self.min_split_chars = settings.get('min_split_chars', 4)

        self.convert_whitespace_to_linebreak = settings.get('whitespaces_to_newline', False)
        self.break_dialog_on_one_line = settings.get('break_dialog_on_one_line', False)
        self.normalise_dialog_tags = settings.get('normalise_dialog_tags', False)
        self.remove_filler_words = settings.get('remove_filler_words', False)

        self.break_long_lines = settings.get('break_long_lines', False)
        self.max_single_line_length = settings.get('max_single_line_length', 40)
        self.min_single_line_length = settings.get('min_single_line_length', 4)

        self.split_dialog_pattern = CompileDialogSplitPattern(self.dialog_marker) if self.break_dialog_on_one_line else None
        self.filler_words_pattern = CompileFillerWordsPattern(settings.get('filler_words')) if self.remove_filler_words else None

        self.split_by_duration = self.max_line_duration.total_seconds() > 0.0

    def PreprocessSubtitles(self, lines : list[SubtitleLine]):
        """
        Pre-process subtitles to make them suitable for translation.

        Will split long lines, add line breaks to dialog, and remove empty lines.
        """
        if not lines:
            return []

        processed = []
        line_number = lines[0].number

        for line in lines:
            line.number = line_number
            self._preprocess_line(line)
            if not line.text:
                continue

            needs_split = self.split_by_duration and line.duration > self.max_line_duration

            if needs_split:
                split_lines = self._split_line_by_duration(line)

                processed.extend(split_lines)
                line_number += len(split_lines)

                if len(split_lines) > 1:
                    new_line_text = ''.join([str(l) for l in split_lines])
                    logging.debug(f"Split line {line.number} into {len(split_lines)} parts:\n{str(line)}-->\n{new_line_text}")
                else:
                    logging.debug(f"Failed to split line {line.number}:\n{str(line)}")
            else:
                processed.append(line)
                line_number += 1

        return processed

    def PostprocessSubtitles(self, lines : list[SubtitleLine]):
        """
        Post-process lines after translation
        """
        if not lines:
            return []

        processed = []
        line_number = lines[0].number

        for line in lines:
            line.number = line_number
            output = self._postprocess_line(line)
            if output:
                processed.extend(output)
                line_number += len(output)

        # TODO: fix minimum durations
        # TODO: fix overlapping start/end times (or merge the lines?)

        return processed

    def _preprocess_line(self, line : SubtitleLine):
        """
        Split dialogs onto separate lines.
        Adjust line breaks to split at punctuation weighted by centrality
        """
        text = line.text.strip()
        if not text:
            return

        # Convert whitespace blocks to newlines
        if self.convert_whitespace_to_linebreak:
            text = ConvertWhitespaceBlocksToNewlines(text)

        # Remove filler words
        if self.remove_filler_words:
            text = RemoveFillerWords(text, self.filler_words_pattern)

        # If the subtitle is a single line, see if it should have line breaks added
        if self.break_dialog_on_one_line:
            text = BreakDialogOnOneLine(text, self.split_dialog_pattern)

        # If the subtitle has multiple lines, make sure dialog markers match
        if self.normalise_dialog_tags:
            text = NormaliseDialogTags(text, self.dialog_marker)

        if text != line.text:
            logging.debug(f"Preprocessed line {line.number}:\n{line.text}\n-->\n{text}")
            line.text = text

    def _postprocess_line(self, line : SubtitleLine):
        """
        Split dialogs onto separate lines.
        Normalise dialog markers.
        Add line breaks to long lines.
        """
        if not line.text:
            return

        text = line.text

        if self.remove_filler_words:
            text = RemoveFillerWords(text, self.filler_words_pattern)

        if self.break_dialog_on_one_line:
            text = BreakDialogOnOneLine(text, self.split_dialog_pattern)

        if self.normalise_dialog_tags:
            text = NormaliseDialogTags(text, self.dialog_marker)

        if self.break_long_lines:
            text = self._break_long_lines(text)

        if text == line.text:
            return [line]

        logging.debug(f"Postprocessed line {line.number}:\n{line.text}\n-->\n{text}")
        processed_line = SubtitleLine.Construct(line.number, line.start, line.end, text)
        return [processed_line]

    def _break_long_lines(self, text):
        """
        Add line breaks to long lines
        """
        if self._compiled_break_sequences is None:
            self._compile_break_sequences()

        max_length = self.max_single_line_length
        min_length = self.min_single_line_length
        break_sequences = self._compiled_break_sequences
        text = BreakLongLine(text, max_line_length=max_length, min_line_length=min_length, break_sequences=break_sequences)
        return text

    def _split_line_by_duration(self, line: SubtitleLine) -> list[SubtitleLine]:
        """
        Recursively split a line into smaller lines based on the duration of the text,
        by choosing a split point from the defined sequences weighted towards the middle.
        """
        result = []
        stack = [line]

        if self._compiled_split_sequences is None:
            self._compile_split_sequences()

        while stack:
            current_line = stack.pop()
            if current_line.duration <= self.max_line_duration or len(current_line.text) < self.min_split_chars * 2:
                result.append(current_line)
                continue

            if (current_line.text[0], current_line.text[-1]) in self.forbidden_start_end_pairs:
                result.append(current_line)
                continue

            split_point = FindSplitPoint(current_line, self._compiled_split_sequences, min_duration=self.min_line_duration, min_split_chars=self.min_split_chars)
            if split_point is None:
                result.append(current_line)
                continue

            split_text = current_line.text[split_point:].strip()
            split_duration = GetProportionalDuration(current_line, len(split_text), self.min_line_duration)
            split_start = current_line.end - split_duration
            split_end = current_line.end

            new_line = SubtitleLine.Construct(current_line.number, current_line.start, split_start - self.min_gap, current_line.text[:split_point])
            split_line = SubtitleLine.Construct(current_line.number, split_start, split_end, split_text)

            stack.extend([split_line, new_line])

        for i, result_line in enumerate(result, start=0):
            result_line.number = line.number + i

        return result

    def _compile_split_sequences(self):
        self._compiled_split_sequences = [regex.compile(seq) for seq in self.split_sequences]

    def _compile_break_sequences(self):
        self._compiled_break_sequences = [regex.compile(seq) for seq in self.break_sequences]


