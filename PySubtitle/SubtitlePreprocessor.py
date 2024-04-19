from datetime import timedelta
import logging
import regex
from PySubtitle.Options import Options
from PySubtitle.SubtitleLine import SubtitleLine

split_sequences = ['\n', '\，', '!', '?', '.', ',', ':', ';', ',']

class SubtitlePreprocessor:
    """
    Helper class to pre-process subtitles to make them suitable for translation.

    Will split long lines, add line breaks and remove empty lines.
    """
    def __init__(self, settings : Options | dict):
        self.max_line_duration = settings.get('max_line_duration', 0.0)
        self.min_line_duration = settings.get('min_line_duration', 0.0)
        self.min_split_length = settings.get('min_split_length', 4)
        self.min_gap = timedelta(seconds=settings.get('min_gap', 0.05))

        self.split_by_duration = self.max_line_duration > 0.0

    def PreprocessSubtitles(self, lines : list[SubtitleLine]):
        """
        Pre-process subtitles to make them suitable for translation.

        Will split long lines, merge short lines, and remove empty lines.
        """
        if not lines:
            return []

        processed = []
        line_number = lines[0].number

        for line in lines:
            self._preprocess_line(line)
            if not line.text:
                continue

            needs_split = self.split_by_duration and line.duration.total_seconds() > self.max_line_duration

            if needs_split:
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

    def _preprocess_line(self, line : SubtitleLine):
        """
        Split dialogs onto separate lines.
        Adjust line breaks to split at punctuation weighted by centrality
        """
        # Remove leading and trailing whitespace
        line.text = line.text.strip()

        # Break line at dialog markers ("- ")
        line_parts = regex.split(r"(?<=\w)- ", line.text)

        if len(line_parts) > 1:
            line.text = '\n'.join(line_parts)

    def _split_line_by_duration(self, line : SubtitleLine) -> list[SubtitleLine]:
        """
        Recursively split a line by finding potential split points and selecting the best one,
        adjusting the duration of the split lines to be proportional to their length as a percentage of the original line.
        """
        if line.duration.total_seconds() <= self.max_line_duration:
            return [line]

        split_point = self._find_split_point(line)
        if split_point is None:
            return [line]

        split_text = line.text[split_point:].strip()
        split_duration = self._get_proportional_duration(len(split_text), line)
        split_start = line.end - split_duration
        split_end = line.end

        line = SubtitleLine.Construct(line.number, line.start, line.end - (split_duration + self.min_gap), line.text[:split_point])

        split_lines : list[SubtitleLine] = self._split_line_by_duration(line)

        split_line = SubtitleLine.Construct(line.number + len(split_lines), split_start, split_end, split_text)
        split_lines.extend(self._split_line_by_duration(split_line))

        return split_lines

    def _find_split_point(self, line : SubtitleLine):
        """
        Find the optimum split point for a subtitle.

        The criteria are:
        Prefer to split at newlines > punctuation > whitespace if possible
        Split as close to the middle as possible
        Neither side of the split should be shorter than the minimum line duration
        """
        line_length = len(line.text)
        split_start_index = self.min_split_length
        split_end_index = line_length - self.min_split_length
        if split_end_index <= split_start_index:
            return None

        for char in split_sequences:
            split_point = None
            split_score = 0

            for index in range(split_start_index, split_end_index):
                if line.text[index] == char:
                    score = self._get_split_score(index, line)
                    if score > split_score:
                        split_point = index + 1
                        split_score = score

            if split_point:
                return split_point

        return None

    def _get_split_score(self, index : int, line : SubtitleLine):
        """
        Calculate the score for a potential split point
        """
        lhs_duration = self._get_proportional_duration(index, line)
        rhs_duration = line.duration - lhs_duration

        lhs_seconds = lhs_duration.total_seconds()
        rhs_seconds = rhs_duration.total_seconds()

        if lhs_seconds < self.min_line_duration or rhs_seconds < self.min_line_duration:
            return 0

        # score approaches 1 for a split point in the middle and 0 at either extremity
        split_ratio = index / len(line.text)
        split_score = 1.0 - abs(split_ratio - 0.5) * 2.0
        return split_score

    def _get_proportional_duration(self, num_characters : int, line : SubtitleLine) -> timedelta:
        """
        Calculate the proportional duration of a character string as a percentage of a subtitle
        """
        line_duration = line.duration.total_seconds()
        line_length = len(line.text)

        if num_characters >= line_length:
            raise ValueError("Proportion is longer than original line")

        length_ratio = num_characters / line_length
        length_seconds = max(line_duration * length_ratio, self.min_line_duration)

        return timedelta(seconds=length_seconds)
