from datetime import timedelta
from os import linesep
from typing import Any
import srt # type: ignore

from PySubtitle.Helpers.Localization import _
from PySubtitle.SubtitleError import SubtitleError
from PySubtitle.Helpers.Time import GetTimeDelta, SrtTimestampToTimedelta, TimedeltaToSrtTimestamp, TimedeltaToText
from PySubtitle.InternalSubtitle import InternalSubtitle

class SubtitleLine:
    """
    Represents a single line, with a number and start and end times plus original text
    and (optionally) an associated translation.
    """
    def __init__(self, line : 'srt.Subtitle|str|SubtitleLine|None', translation : str|None = None, original : str|None = None):
        self._item : InternalSubtitle|None = None
        self.translation : str|None = translation
        self.original : str|None = original
        self._duration : timedelta|None = None

        if isinstance(line, SubtitleLine):
            self._item = line._item.copy() if line._item else None
            self._duration = line._duration
            self.original = original if original is not None else line.original
            self.translation = translation if translation is not None else line.translation
        elif line is not None:
            self.item = line

    def __str__(self) -> str:
        return self.item.to_srt() if self.item else "Null SubtitleLine"

    def __repr__(self) -> str:
        return f"[Line {self.number}] {TimedeltaToText(self.start)}, {repr(self.text)}"

    def __eq__(self, other : 'Any|SubtitleLine') -> bool:
        return self._item == other._item if isinstance(other, SubtitleLine) else False

    @property
    def key(self) -> int | str:
        return self.number if self.number else str(self.start)

    @property
    def number(self) -> int:
        return self._item.index if self._item else 0

    @property
    def text(self) -> str|None:
        return self._item.content if self._item else None

    @property
    def text_normalized(self) -> str|None:
        return self.text.replace(linesep, '\n').strip() if self.text else None

    @property
    def start(self) -> timedelta:
        return self._item.start if self._item else timedelta(seconds=0)

    @property
    def srt_start(self) -> str:
        return TimedeltaToSrtTimestamp(self.start) or "00:00.00,000"

    @property
    def txt_start(self) -> str:
        return TimedeltaToText(self.start) or _("Invalid timestamp")

    @property
    def end(self) -> timedelta:
        return self._item.end if self._item else timedelta(seconds=0)

    @property
    def srt_end(self) -> str:
        return TimedeltaToSrtTimestamp(self.end) or "00:00.00,000"

    @property
    def txt_end(self) -> str:
        return TimedeltaToText(self.end) or _("Invalid timestamp")

    @property
    def duration(self) -> timedelta:
        if not self._duration:
            self._duration = self.end - self.start if self.start is not None and self.end else timedelta(seconds=0)
        return self._duration

    @property
    def srt_duration(self) -> str:
        return TimedeltaToText(self.duration)

    @property
    def line(self) -> str | None:
        if not self._item or self._item.start is None or self._item.end is None:
            return None

        return self._item.to_srt(strict=False)

    @property
    def translated(self) -> 'SubtitleLine|None':
        if self.translation is None:
            return None
        return SubtitleLine.Construct(self.number, self.start, self.end, self.translation)

    @property
    def item(self) -> InternalSubtitle:
        return self._item or InternalSubtitle(index=None, start=timedelta(seconds=0), end=timedelta(seconds=0), content="Invalid Line")

    @item.setter
    def item(self, item : srt.Subtitle | str):
        self._item = CreateInternalSubtitle(item)
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

    @duration.setter
    def duration(self, duration : timedelta|str):
        if self._item and self._item.start is not None:
            tdelta : timedelta|Exception|None = GetTimeDelta(duration)
            if isinstance(tdelta, Exception):
                raise SubtitleError(f"Invalid duration", error=tdelta)

            self._duration = tdelta or timedelta(seconds=0)
            self._item.end = self._item.start + self._duration

    @translated.setter
    def translated(self, translated : 'SubtitleLine|srt.Subtitle|str|None'):
        self.translation = SubtitleLine(translated).text if translated else None

    @classmethod
    def Construct(cls, number : int|str|None, start : timedelta|str|None, end : timedelta|str|None, text : str, original : str|None = None):
        i_number = int(number) if number else None
        t_start : timedelta|Exception|None = GetTimeDelta(start)
        t_end : timedelta|Exception|None = GetTimeDelta(end)
        if isinstance(t_start, Exception):
            raise t_start
        if isinstance(t_end, Exception):
            raise t_end

        legal_text : str = InternalSubtitle.make_legal_content(text.strip()) if text else ""
        legal_original = InternalSubtitle.make_legal_content(original.strip()) if original else ""
        item = InternalSubtitle(i_number, t_start, t_end, legal_text)
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

def CreateInternalSubtitle(item : srt.Subtitle | SubtitleLine | str) -> InternalSubtitle|None:
    """
    Try to construct an InternalSubtitle from the argument
    """
    if hasattr(item, 'item'):
        item = getattr(item, 'item')

    if isinstance(item, srt.Subtitle):
        return InternalSubtitle(
            index=item.index,
            start=item.start,
            end=item.end,
            content=item.content,
            proprietary=getattr(item, 'proprietary', '')
        )
    
    if isinstance(item, InternalSubtitle):
        return item.copy()

    line = str(item).strip()
    match = srt.SRT_REGEX.match(line)
    if match:
        raw_index, raw_start, raw_end, proprietary, content = match.groups()
        index = int(raw_index) if raw_index else None
        start = SrtTimestampToTimedelta(raw_start)
        end = SrtTimestampToTimedelta(raw_end)
        return InternalSubtitle(index, start, end, content, proprietary or "")

    if item is not None:
        raise ValueError(_("Invalid SRT line: {line}").format(line=line))

    return None


def CreateSrtSubtitle(item: InternalSubtitle | SubtitleLine | srt.Subtitle | str) -> srt.Subtitle|None:
    """
    Convert InternalSubtitle to srt.Subtitle for backward compatibility.
    This function is used for file I/O operations that still need srt.Subtitle objects.
    """
    if isinstance(item, srt.Subtitle):
        return item
    
    if isinstance(item, SubtitleLine):
        internal = item._item
        if not internal:
            return None
        return srt.Subtitle(
            index=internal.index,
            start=internal.start,
            end=internal.end,
            content=internal.content,
            proprietary=internal.proprietary
        )
    
    if isinstance(item, InternalSubtitle):
        return srt.Subtitle(
            index=item.index,
            start=item.start,
            end=item.end,
            content=item.content,
            proprietary=item.proprietary
        )
    
    # Try to parse string
    internal = CreateInternalSubtitle(item)
    if internal:
        return srt.Subtitle(
            index=internal.index,
            start=internal.start,
            end=internal.end,
            content=internal.content,
            proprietary=internal.proprietary
        )
    
    return None