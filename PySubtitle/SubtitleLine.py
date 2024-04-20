from datetime import timedelta
from os import linesep
import srt

from PySubtitle.Helpers import GetTimeDelta, TimeDeltaToText

class SubtitleLine:
    """
    Represents a single line, with a number and start and end times plus original text
    and (optionally) an associated translation.
    """
    def __init__(self, line : srt.Subtitle | str, translation : str = None, original : str = None):
        self.item = line
        self.translation = translation
        self.original = original

    def __str__(self):
        return self.item.to_srt() if self.item else None

    def __repr__(self):
        return f"Line({TimeDeltaToText(self.start) if self.start is not None else self.number}, {repr(self.text)})"

    @property
    def key(self) -> int | str:
        return self.number if self.number else str(self.start)

    @property
    def number(self) -> int:
        return self._item.index if self._item else None

    @property
    def text(self) -> str:
        return self._item.content if self._item else None

    @property
    def text_normalized(self) -> str:
        return self.text.replace(linesep, '\n') if self.text else None

    @property
    def start(self) -> timedelta:
        return self._item.start if self._item else None

    @property
    def srt_start(self) -> str:
        return TimeDeltaToText(self.start) if self.start is not None else None

    @property
    def end(self) -> timedelta:
        return self._item.end if self._item else None

    @property
    def srt_end(self) -> str:
        return TimeDeltaToText(self.end) if self.end else None

    @property
    def duration(self) -> timedelta:
        if not self._duration:
            self._duration = self.end - self.start if self.start is not None and self.end else timedelta(seconds=0)
        return self._duration

    @duration.setter
    def duration(self, duration):
        if self._item and self._item.start:
            self._duration = GetTimeDelta(duration)
            self._item.end = self._item.start + self._duration

    @property
    def srt_duration(self) -> str:
        return TimeDeltaToText(self.duration)

    @property
    def line(self) -> str | None:
        return self._item.to_srt() if self._item and self._item.start and self._item.end and self._item.content else None

    @property
    def translated(self) -> srt.Subtitle | None:
        if not self._item or not self.translation:
            return None
        return SubtitleLine.Construct(self.number, self.start, self.end, self.translation)

    @property
    def item(self) -> srt.Subtitle:
        return self._item

    @item.setter
    def item(self, item):
        if isinstance(item, SubtitleLine):
            item = item.item

        self._item : srt.Subtitle = CreateSrtSubtitle(item)
        self._duration = None

    @number.setter
    def number(self, value):
        if self._item:
            self._item.index = value

    @text.setter
    def text(self, text):
        if self._item:
            self._item.content = text

    @start.setter
    def start(self, time):
        if self._item:
            self._item.start = GetTimeDelta(time)
            self._duration = None

    @end.setter
    def end(self, time):
        if self._item:
            self._item.end = GetTimeDelta(time)
            self._duration = None

    def GetProportionalDuration(self, num_characters : int, min_duration : timedelta = None) -> timedelta:
        """
        Calculate the proportional duration of a character string as a percentage of a subtitle
        """
        line_duration = self.duration.total_seconds()
        line_length = len(self.text)

        if num_characters >= line_length:
            raise ValueError("Proportion is longer than original line")

        length_ratio = num_characters / line_length
        length_seconds = line_duration * length_ratio

        if min_duration:
            length_seconds = max(length_seconds, min_duration.total_seconds())

        return timedelta(seconds=length_seconds)

    @classmethod
    def Construct(cls, number : int, start : timedelta | str, end : timedelta | str, text : str, original : str = None):
        number = int(number) if number else None
        start : timedelta = GetTimeDelta(start)
        end : timedelta = GetTimeDelta(end)
        text : str = srt.make_legal_content(text.strip()) if text else None
        original = srt.make_legal_content(original.strip()) if original else None
        item = srt.Subtitle(number, start, end, text)
        return SubtitleLine(item, original=original)

    @classmethod
    def FromDictionary(cls, values):
        """
        Construct a SubtitleLine from a dictionary.
        """
        return SubtitleLine.Construct(
            values.get('number') or values.get('index'),
            values.get('start'),
            values.get('end'),
            values.get('body') or values.get('original'),
            values.get('original'))

    @classmethod
    def FromMatch(cls, match):
        """
        Construct a SubtitleLine from a regex match.

        Really should use named groups, but findall doesn't seem to preserve the names.
        """
        if len(match) > 3:
            number, start, end, body = match
        else:
            start, end, body = match
            number = None

        return SubtitleLine.Construct(number, start.strip(), end.strip(), body.strip())

def CreateSrtSubtitle(item : srt.Subtitle | SubtitleLine | str) -> srt.Subtitle:
    """
    Try to construct an srt.Subtitle from the argument
    """
    if hasattr(item, 'item'):
        item = item.item

    if not isinstance(item, srt.Subtitle):
        line = str(item).strip()
        match = srt.SRT_REGEX.match(line)
        if match:
            raw_index, raw_start, raw_end, proprietary, content = match.groups()
            index = int(raw_index) if raw_index else None
            start = srt.srt_timestamp_to_timedelta(raw_start)
            end = srt.srt_timestamp_to_timedelta(raw_end)
            item = srt.Subtitle(index, start, end, content, proprietary)

    return item