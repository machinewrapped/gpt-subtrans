from datetime import timedelta
import logging
from os import linesep
from typing import Any
import srt

from PySubtitle.SubtitleError import SubtitleError
from PySubtitle.Helpers.Time import GetTimeDelta, TimeDeltaToText

class SubtitleLine:
    """
    Represents a single line, with a number and start and end times plus original text
    and (optionally) an associated translation.
    """
    def __init__(self, line : srt.Subtitle|str|'SubtitleLine'|None, translation : str|None = None, original : str|None = None):
        if isinstance(line, SubtitleLine):
            self._item : srt.Subtitle = line._item
            self._duration : timedelta|None = line._duration
            self.translation : str|None = translation or line.translation
            self.original : str|None = original or line.original
        elif line is not None:
            self.item = line
            self.translation : str|None = translation
            self.original : str|None = original
        else:
            self._item = srt.Subtitle(0, timedelta(seconds=0), timedelta(seconds=0), "Invalid line")
            self._duration : timedelta|None = None
            self.translation : str|None = translation
            self.original : str|None = original

    def __str__(self) -> str:
        return self.item.to_srt() if self.item else "Null SubtitleLine"

    def __repr__(self):
        return f"[Line {self.number}] {TimeDeltaToText(self.start)}, {repr(self.text)}"

    def __eq__(self, other : Any|'SubtitleLine') -> bool:
        return self._item == other._item if isinstance(other, SubtitleLine) else False

    @property
    def key(self) -> int | str:
        return self.number if self.number else str(self.start)

    @property
    def number(self) -> int|None:
        return self._item.index if self._item else None

    @property
    def text(self) -> str|None:
        return self._item.content if self._item else None

    @property
    def text_normalized(self) -> str|None:
        return self.text.replace(linesep, '\n') if self.text else None

    @property
    def start(self) -> timedelta|None:
        return self._item.start if self._item else None

    @property
    def srt_start(self) -> str|None:
        return srt.timedelta_to_srt_timestamp(self.start) if self.start is not None else None

    @property
    def txt_start(self) -> str|None:
        return TimeDeltaToText(self.start) if self.start is not None else None

    @property
    def end(self) -> timedelta|None:
        return self._item.end if self._item else None

    @property
    def srt_end(self) -> str|None:
        return srt.timedelta_to_srt_timestamp(self.end) if self.end else None

    @property
    def txt_end(self) -> str|None:
        return TimeDeltaToText(self.end) if self.end is not None else None

    @property
    def duration(self) -> timedelta|None:
        if not self._duration:
            self._duration = self.end - self.start if self.start is not None and self.end else timedelta(seconds=0)
        return self._duration

    @duration.setter
    def duration(self, duration : timedelta|str):
        if self._item and self._item.start is not None:
            tdelta : timedelta|Exception|None = GetTimeDelta(duration)
            if isinstance(tdelta, Exception):
                raise SubtitleError(f"Invalid duration", error=tdelta)

            self._duration = tdelta or timedelta(seconds=0)
            self._item.end = self._item.start + self._duration

    @property
    def srt_duration(self) -> str:
        return TimeDeltaToText(self.duration)

    @property
    def line(self) -> str | None:
        if not self._item or self._item.start is None or self._item.end is None:
            return None

        return self._item.to_srt(strict=False)

    @property
    def translated(self) -> 'None|SubtitleLine':
        if self.translation is None:
            return None
        return SubtitleLine.Construct(self.number, self.start, self.end, self.translation)

    @property
    def item(self) -> srt.Subtitle:
        return self._item

    @item.setter
    def item(self, item : srt.Subtitle | str):
        self._item : srt.Subtitle = CreateSrtSubtitle(item)
        self._duration = None

    @number.setter
    def number(self, value : int):
        if self._item:
            self._item.index = value

    @text.setter
    def text(self, text : str):
        if self._item:
            self._item.content = text

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
    def translated(self, translated : 'srt.Subtitle|str|SubtitleLine'):
        self.translation = SubtitleLine(translated).text

    @classmethod
    def Construct(cls, number : int|str|None, start : timedelta|str|None, end : timedelta|str|None, text : str, original : str|None = None):
        i_number = int(number) if number else None
        t_start : timedelta|Exception|None = GetTimeDelta(start)
        t_end : timedelta|Exception|None = GetTimeDelta(end)
        if t_start is Exception:
            raise t_start
        if t_end is Exception:
            raise t_end

        legal_text : str = srt.make_legal_content(text.strip()) if text else ""
        legal_original = srt.make_legal_content(original.strip()) if original else ""
        item = srt.Subtitle(i_number, t_start, t_end, legal_text)
        return SubtitleLine(item, original=legal_original)

    @classmethod
    def FromDictionary(cls, values : dict[str, Any]) -> 'SubtitleLine':
        """
        Construct a SubtitleLine from a dictionary.
        """
        return SubtitleLine.Construct(
            values.get('number') or values.get('index') or values.get('id') or -1,
            values.get('start') or timedelta(seconds=0),
            values.get('end') or timedelta(seconds=0),
            values.get('body') or values.get('original') or values.get('text') or "** Missing text **",
            values.get('original'))

    @classmethod
    def FromMatch(cls, match : tuple[str, str, str, str]) -> 'SubtitleLine':
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
        elif item is not None:
            logging.warning(f"Failed to parse line: {line}")

    return item