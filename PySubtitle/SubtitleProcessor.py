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
        self.split_sequences = ["\n", self.dialog_marker, "!", "?", ".", "，", "、", "…", "。", ",", "﹑", ":", ";", ",", "   "]

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
            self._preprocess_line(line)
            if not line.text:
                continue

            needs_split = self.split_by_duration and line.duration > self.max_line_duration

            if needs_split and self._can_split(line):
                split_lines = self._split_line_by_duration(line)

                for out_line in split_lines:
                    out_line.number = line_number
                    processed.append(out_line)
                    line_number += 1

                if len(split_lines) > 1:
                    new_line_text = '\n'.join([str(l) for l in split_lines])
                    logging.debug(f"Split line {line.number} into {len(split_lines)} parts:\n{str(line)}\n-->\n{new_line_text}")
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

    def _split_line_by_duration(self, line : SubtitleLine) -> list[SubtitleLine]:
        """
        Recursively split a line by finding potential split points and selecting the best one,
        adjusting the duration of the split lines to be proportional to their length as a percentage of the original line.
        """
        if line.duration <= self.max_line_duration:
            return [line]

        split_point = _find_break_point(line, self.split_sequences, min_duration=self.min_line_duration, min_split_chars=self.min_split_chars)
        if split_point is None:
            return [line]

        split_text = line.text[split_point:].strip()
        split_duration = line.GetProportionalDuration(len(split_text), self.min_line_duration)
        split_start = line.end - split_duration
        split_end = line.end

        line = SubtitleLine.Construct(line.number, line.start, line.end - (split_duration + self.min_gap), line.text[:split_point])

        split_lines : list[SubtitleLine] = self._split_line_by_duration(line)

        split_line = SubtitleLine.Construct(line.number + len(split_lines), split_start, split_end, split_text)
        split_lines.extend(self._split_line_by_duration(split_line))

        return split_lines

def _find_break_point(line: SubtitleLine, break_sequences: list[str], min_duration: timedelta, min_split_chars: int):
    """
    Find the optimum split point for a subtitle.

    The criteria are:
    Take break sequences as priority order, find the first matching sequence.
    Break at the occurence that is as close to the middle as possible.
    Neither side of the split should be shorter than the minimum line duration
    If multiple instances of a split sequence are adjacent, split at the last one
    """
    line_length = len(line.text)
    start_index = min_split_chars
    end_index = line_length - min_split_chars
    if end_index <= start_index:
        return None

    for seq in break_sequences:
        best_break_point = None
        best_break_score = 0

        # Find all occurrences of the sequence in the allowable range
        index = line.text.find(seq, start_index)
        while index != -1 and index < end_index:
            # Compute the score after this sequence
            break_index = index + len(seq)
            score = _get_split_score(break_index, line, min_duration)

            if score > best_break_score:
                best_break_point = break_index
                best_break_score = score

            index = line.text.find(seq, index + 1)

        if best_break_point is not None:
            return best_break_point

    return None

def _get_split_score(index : int, line : SubtitleLine, min_duration : timedelta):
    """
    Calculate the score for a potential split point
    """
    lhs_duration = line.GetProportionalDuration(index, min_duration=min_duration)
    rhs_duration = line.duration - lhs_duration

    lhs_seconds = lhs_duration.total_seconds()
    rhs_seconds = rhs_duration.total_seconds()
    min_seconds = min_duration.total_seconds()

    if lhs_seconds < min_seconds or rhs_seconds < min_seconds:
        return 0

    # score approaches 1 for a split point in the middle and 0 at either extremity
    split_ratio = index / len(line.text)
    split_score = 1.0 - abs(split_ratio - 0.5) * 2.0
    return split_score

