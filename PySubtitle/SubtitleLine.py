import logging
import pysubs2
import regex
import srt

from datetime import timedelta
from os import linesep

from PySubtitle.Helpers.Text import NormaliseNewlines
from PySubtitle.Helpers.Time import GetTimeDelta, TimeDeltaToSrtTimestamp, TimeDeltaToText

srt_template = "{0}\n{1} --> {2}\n{3}\n\n"

class SubtitleLine:
    """
    Represents a single line, with a number and start and end times plus original text
    and (optionally) an associated translation.
    """
    class Item:
        """
        Represents a single line, with a number and start and end times plus text
        """

        def __init__(self, index : int, start : timedelta, end : timedelta, text : str):
            self.index : int = index
            self.start : timedelta = start
            self.end : timedelta = end
            self.text : str = NormaliseNewlines(text)

        def to_srt(self) -> str:
            return srt_template.format(self.index, TimeDeltaToSrtTimestamp(self.start), TimeDeltaToSrtTimestamp(self.end), self.text or "\n")

        def __eq__(self, other):
            if not isinstance(other, SubtitleLine.Item):
                return False
            return self.index == other.index and self.start == other.start and self.end == other.end and self.text == other.text

    def __init__(self, line : Item | str, index : int = None, translation : str = None, original : str = None):
        if isinstance(line, SubtitleLine):
            self._item = line._item
            self._duration = line._duration
            self.translation = translation or line.translation
            self.original = original or line.original
        else:
            self._item = CreateSubtitleItem(line, index)
            self._duration = None
            self.translation = translation
            self.original = original

    def __str__(self):
        return self.item.to_srt() if self.item else None

    def __repr__(self):
        return f"[Line {self.number}] {TimeDeltaToText(self.start)}, {repr(self.text)}"

    def __eq__(self, other):
        return self._item == other._item if isinstance(other, SubtitleLine) else False

    @property
    def key(self) -> int | str:
        return self.number if self.number else str(self.start)

    @property
    def number(self) -> int:
        return self._item.index if self._item else None

    @property
    def text(self) -> str:
        return self._item.text if self._item else None

    @property
    def text_normalized(self) -> str:
        return self.text.replace(linesep, '\n') if self.text else None

    @property
    def start(self) -> timedelta:
        return self._item.start if self._item else None

    @property
    def srt_start(self) -> str:
        return TimeDeltaToSrtTimestamp(self.start) if self.start is not None else None

    @property
    def txt_start(self) -> str:
        return TimeDeltaToText(self.start) if self.start is not None else None

    @property
    def end(self) -> timedelta:
        return self._item.end if self._item else None

    @property
    def srt_end(self) -> str:
        return TimeDeltaToSrtTimestamp(self.end) if self.end else None

    @property
    def txt_end(self) -> str:
        return TimeDeltaToText(self.end) if self.end is not None else None

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
    def txt_duration(self) -> str:
        return TimeDeltaToText(self.duration)

    @property
    def line(self) -> str | None:
        if not self._item or not self._item.start or not self._item.end:
            return None

        return self._item.to_srt()

    @property
    def translated(self) -> Item | None:
        if self._item is None or self.translation is None:
            return None
        return SubtitleLine.Construct(self.number, self.start, self.end, self.translation)

    @property
    def item(self) -> Item:
        return self._item

    @item.setter
    def item(self, item : Item | str):
        self._item : SubtitleLine.Item = CreateSubtitleItem(item)
        self._duration = None

    @number.setter
    def number(self, value : int):
        if self._item:
            self._item.index = value

    @text.setter
    def text(self, text : str):
        if self._item:
            self._item.text = text

    @start.setter
    def start(self, time : timedelta | str):
        if self._item:
            self._item.start = GetTimeDelta(time)
            self._duration = None

    @end.setter
    def end(self, time : timedelta | str):
        if self._item:
            self._item.end = GetTimeDelta(time)
            self._duration = None

    @translated.setter
    def translated(self, translated):
        self.translation = SubtitleLine(translated).text

    @classmethod
    def Construct(cls, number : int, start : timedelta | str, end : timedelta | str, text : str, original : str = None, translation : str = None):
        number = int(number) if number else None
        start : timedelta = GetTimeDelta(start)
        end : timedelta = GetTimeDelta(end)
        text : str = srt.make_legal_content(text.strip()) if text else ""
        original = srt.make_legal_content(original.strip()) if original else ""
        item = SubtitleLine.Item(number, start, end, text)
        return SubtitleLine(item, index=number, original=original, translation=translation)

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
            values.get('original'),
            values.get('translation'))

    @classmethod
    def FromMatch(cls, match : regex.Match):
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

def CreateSubtitleItem(item : SubtitleLine.Item | SubtitleLine | srt.Subtitle | pysubs2.SSAEvent | dict | str, index : int | None) -> SubtitleLine.Item | None:
    """
    Try to construct a SubtitleLine.Item from the argument
    """
    if item is None:
        return None

    if isinstance(item, SubtitleLine.Item):
        return item

    if isinstance(item, SubtitleLine) or hasattr(item, 'item'):
        return item.item

    if isinstance(item, srt.Subtitle):
        return SubtitleLine.Item(item.index, item.start, item.end, item.content)

    if isinstance(item, pysubs2.SSAEvent):
        return SubtitleLine.Item(index=index, start=timedelta(milliseconds=item.start), end=timedelta(milliseconds=item.end), text=item.text)

    if isinstance(item, dict):
        return SubtitleLine.FromDictionary(item)

    line = str(item).strip()
    match = srt.SRT_REGEX.match(line)
    if match:
        raw_index, raw_start, raw_end, proprietary, content = match.groups()
        index = int(raw_index) if raw_index else None
        start = GetTimeDelta(raw_start)
        end = GetTimeDelta(raw_end)
        item = SubtitleLine.Item(index, start, end, content)
    else:
        logging.warning(f"Failed to parse line: {line}")

    return item
