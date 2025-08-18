from datetime import timedelta
from os import linesep
from typing import Any
import regex

from PySubtitle.Helpers.Localization import _
from PySubtitle.SubtitleError import SubtitleError
from PySubtitle.Helpers.Time import GetTimeDelta, SrtTimestampToTimedelta, TimedeltaToSrtTimestamp, TimedeltaToText

class SubtitleLine:
    """
    Represents a single subtitle line with timing, content, and metadata.
    This is the internal representation used throughout the application.
    """
    def __init__(self, line : 'SubtitleLine|str|dict|None' = None, translation : str|None = None, original : str|None = None):
        # Core subtitle properties 
        self.index: int | None = None
        self.start: timedelta = timedelta(seconds=0)
        self.end: timedelta = timedelta(seconds=0)
        self.content: str = ""
        self.proprietary: str = ""
        
        # Additional properties
        self.translation : str|None = translation
        self.original : str|None = original
        self._duration : timedelta|None = None

        if isinstance(line, SubtitleLine):
            # Copy from another SubtitleLine
            self.index = line.index
            self.start = line.start
            self.end = line.end
            self.content = line.content
            self.proprietary = line.proprietary
            self._duration = line._duration
            self.original = original if original is not None else line.original
            self.translation = translation if translation is not None else line.translation
        elif isinstance(line, dict):
            # Construct from dictionary
            if 'line' in line:
                # Backwards compatibility: extract from line property 
                self._parse_from_string(str(line['line']))
            else:
                # New format: use individual properties
                self.index = line.get('index') or line.get('number')
                start_time = line.get('start')
                if start_time is not None:
                    self.start = GetTimeDelta(start_time) or timedelta(seconds=0)
                end_time = line.get('end')
                if end_time is not None:
                    self.end = GetTimeDelta(end_time) or timedelta(seconds=0)
                self.content = line.get('content') or line.get('text') or ""
                self.proprietary = line.get('proprietary', "")
            
            # Override with provided translation/original if specified
            self.translation = translation if translation is not None else line.get('translation')
            self.original = original if original is not None else line.get('original')
        elif line is not None:
            # Parse from string
            self._parse_from_string(str(line))

    def _parse_from_string(self, line_str: str) -> None:
        """Parse subtitle line from basic SRT format string."""
        line = line_str.strip()
        
        if not line:
            return
        
        # Parse basic SRT format: number\ntimestamp\ncontent
        # Pattern matches: index, start --> end, content (multiline)
        srt_pattern = regex.compile(
            r'^(?P<index>\d+)\s*\n'
            r'(?P<start>\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(?P<end>\d{2}:\d{2}:\d{2},\d{3})\s*\n'
            r'(?P<content>.*?)$',
            regex.DOTALL
        )
        
        match = srt_pattern.match(line)
        if match:
            self.index = int(match.group('index'))
            try:
                self.start = SrtTimestampToTimedelta(match.group('start'))
                self.end = SrtTimestampToTimedelta(match.group('end'))
            except ValueError:
                # If timestamp parsing fails, keep defaults and store raw content
                pass
            self.content = match.group('content').strip()
        else:
            # If doesn't match SRT format, store as raw content
            self.content = line

    def __str__(self) -> str:
        return self.to_srt() if self.start is not None and self.end is not None else "Invalid SubtitleLine"

    def __repr__(self) -> str:
        return f"[Line {self.number}] {TimedeltaToText(self.start)}, {repr(self.text)}"

    def __eq__(self, other : 'Any|SubtitleLine') -> bool:
        if not isinstance(other, SubtitleLine):
            return False
        return (self.index == other.index and 
                self.start == other.start and 
                self.end == other.end and 
                self.content == other.content and
                self.proprietary == other.proprietary)

    def copy(self) -> 'SubtitleLine':
        """Create a copy of this subtitle line."""
        new_line = SubtitleLine()
        new_line.index = self.index
        new_line.start = self.start
        new_line.end = self.end
        new_line.content = self.content
        new_line.proprietary = self.proprietary
        new_line.translation = self.translation
        new_line.original = self.original
        new_line._duration = self._duration
        return new_line

    def to_srt(self, strict: bool = True) -> str:
        """
        Convert to SRT format string for output.
        """
        if self.start is None or self.end is None:
            if strict:
                raise ValueError("Cannot convert subtitle with missing timestamps to SRT")
            return ""
        
        start_str = TimedeltaToSrtTimestamp(self.start) or "00:00:00,000"
        end_str = TimedeltaToSrtTimestamp(self.end) or "00:00:00,000"
        
        # Format: number\nstart --> end\ncontent\n\n
        parts = []
        if self.index is not None:
            parts.append(str(self.index))
        parts.append(f"{start_str} --> {end_str}")
        if self.content:
            parts.append(self.content)
        if self.proprietary:
            parts.append(self.proprietary)
        
        return "\n".join(parts)

    @staticmethod
    def make_legal_content(content: str) -> str:
        """
        Make content legal for subtitle format.
        """
        if not content:
            return ""
        
        # Remove or replace problematic characters that could break subtitle parsing
        content = content.strip()
        
        # Replace problematic sequences that could interfere with SRT parsing
        content = content.replace("-->", "→")  # Replace SRT timestamp separator
        
        # Normalize line endings
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        
        return content

    @property
    def key(self) -> int | str:
        return self.number if self.number else str(self.start)

    @property
    def number(self) -> int:
        return self.index or 0

    @property
    def text(self) -> str|None:
        return self.content

    @property
    def text_normalized(self) -> str|None:
        return self.text.replace(linesep, '\n').strip() if self.text else None

    @property
    def srt_start(self) -> str:
        return TimedeltaToSrtTimestamp(self.start) or "00:00.00,000"

    @property
    def txt_start(self) -> str:
        return TimedeltaToText(self.start) or _("Invalid timestamp")

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
        if self.start is None or self.end is None:
            return None
        return self.to_srt(strict=False)

    @property
    def translated(self) -> 'SubtitleLine|None':
        if self.translation is None:
            return None
        return SubtitleLine.Construct(self.number, self.start, self.end, self.translation)

    @number.setter
    def number(self, value : int):
        self.index = value

    @text.setter
    def text(self, text : str):
        self.content = text

    def set_start(self, time : timedelta | str):
        """Set the start time, handling string conversion."""
        new_time = GetTimeDelta(time, raise_exception=True)
        if isinstance(new_time, Exception):
            raise SubtitleError(f"Invalid start time: {time}", error=new_time)
        if new_time is not None:
            self.start = new_time
            self._duration = None

    def set_end(self, time : timedelta | str):
        """Set the end time, handling string conversion.""" 
        new_time = GetTimeDelta(time, raise_exception=True)
        if isinstance(new_time, Exception):
            raise SubtitleError(f"Invalid end time: {time}", error=new_time)
        if new_time is not None:
            self.end = new_time
            self._duration = None

    def set_duration(self, duration : timedelta|str):
        """Set the duration and update end time accordingly."""
        if self.start is not None:
            tdelta : timedelta|Exception|None = GetTimeDelta(duration)
            if isinstance(tdelta, Exception):
                raise SubtitleError(f"Invalid duration", error=tdelta)

            self._duration = tdelta or timedelta(seconds=0)
            self.end = self.start + self._duration

    @translated.setter
    def translated(self, translated : 'SubtitleLine|str|None'):
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

        legal_text : str = SubtitleLine.make_legal_content(text.strip()) if text else ""
        legal_original = SubtitleLine.make_legal_content(original.strip()) if original else ""
        
        line = SubtitleLine()
        line.index = i_number
        line.start = t_start or timedelta(seconds=0)
        line.end = t_end or timedelta(seconds=0)
        line.content = legal_text
        line.original = legal_original
        return line

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