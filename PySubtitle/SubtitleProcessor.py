import logging
import regex
from datetime import timedelta

from PySubtitle.Helpers.Text import ConvertWhitespaceBlocksToNewlines, BreakDialogOnOneLine, NormaliseDialogTags, ContainsTags
from PySubtitle.Options import Options
from PySubtitle.SubtitleLine import SubtitleLine

class SubtitleProcessor:
    """
    Helper class to pre-process subtitles to make them suitable for translation.

    Will split long lines, add line breaks and remove empty lines.
    """
    def __init__(self, settings : Options | dict):
        self.dialog_marker = "- "
        self.split_sequences = [
            r"\n",  # Newline has the highest priority
            regex.escape(self.dialog_marker),  # Dialog marker
            r"(?=\([^)]*\)|\[[^\]]*\])",  # Look ahead to find a complete parenthetical or bracketed block to split before
            r"[!?？！]+",  # Sequence of punctuation like '!', '?'
            r"[.。…]+",  # Sequence of sentence punctuation
            r"[,，、﹑]",  # Various forms of commas
            r"[:;]",  # Colon and semicolon
            r"[–—]+",  # Dashes
            r" {3,}"  # Three or more spaces
        ]
        self._compiled_split_sequences = None

        self.max_line_duration = timedelta(seconds = settings.get('max_line_duration', 0.0))
        self.min_line_duration = timedelta(seconds = settings.get('min_line_duration', 0.0))
        self.min_gap = timedelta(seconds=settings.get('min_gap', 0.05))
        self.min_split_chars = settings.get('min_split_chars', 4)

        self.convert_whitespace_to_linebreak = settings.get('whitespaces_to_newline', False)
        self.break_dialog_on_one_line = settings.get('break_dialog_on_one_line', False)
        self.normalise_dialog_tags = settings.get('normalise_dialog_tags', False)

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

            if needs_split and self._can_split(line):
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

    def _can_split(self, line : SubtitleLine) -> bool:
        """ Check if a line can be split """
        return not ContainsTags(line.text)

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

        # If the subtitle is a single line, see if it should have line breaks added
        if self.break_dialog_on_one_line and self.dialog_marker in text:
            text = BreakDialogOnOneLine(text, self.dialog_marker)

        # If the subtitle has multiple lines, make sure dialog markers match
        if self.normalise_dialog_tags:
            text = NormaliseDialogTags(text, self.dialog_marker)

        if text != line.text:
            logging.debug(f"Preprocessed line {line.number}:\n{line.text}\n-->\n{text}")
            line.text = text

    def _split_line_by_duration(self, line: SubtitleLine) -> list[SubtitleLine]:
        result = []
        stack = [line]

        if self._compiled_split_sequences is None:
            self._compiled_split_sequences = [regex.compile(seq) for seq in self.split_sequences]

        while stack:
            current_line = stack.pop()
            if current_line.duration <= self.max_line_duration:
                result.append(current_line)
                continue

            split_point = _find_break_point(current_line, self._compiled_split_sequences, min_duration=self.min_line_duration, min_split_chars=self.min_split_chars)
            if split_point is None:
                result.append(current_line)
                continue

            split_text = current_line.text[split_point:].strip()
            split_duration = current_line.GetProportionalDuration(len(split_text), self.min_line_duration)
            split_start = current_line.end - split_duration
            split_end = current_line.end

            new_line = SubtitleLine.Construct(current_line.number, current_line.start, split_start - self.min_gap, current_line.text[:split_point])
            split_line = SubtitleLine.Construct(current_line.number, split_start, split_end, split_text)

            stack.extend([split_line, new_line])

        for i, line in enumerate(result, start=0):
            line.number = line.number + i

        return result

def _find_break_point(line: SubtitleLine, break_sequences: list, min_duration: timedelta, min_split_chars: int):
    """
    Find the optimal break point for a subtitle.

    The criteria are:
    Take break sequences as priority order, find the first matching sequence.
    Break at the occurence that is as close to the middle as possible.
    Neither side of the split should be shorter than the minimum line duration
    """
    line_length = len(line.text)
    start_index = min_split_chars
    end_index = line_length - min_split_chars
    if end_index <= start_index:
        return None

    middle_index = line_length // 2

    for seq in break_sequences:
        matches = list(seq.finditer(line.text))
        if not matches:
            continue

        # Find the match that is closest to the middle of the text
        best_match = min(matches, key=lambda m: abs(m.end() - middle_index))
        split_index = best_match.end()
        split_time = line.GetProportionalDuration(split_index, min_duration)
        if split_time < min_duration or (line.duration - split_time) < min_duration:
            continue

        return split_index

    return None

