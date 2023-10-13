from datetime import timedelta
from os import linesep
import srt

from PySubtitle.Helpers import CreateSrtSubtitle, GetTimeDelta

class SubtitleLine:
    """
    Represents a single line, with a number and start and end times plus original text 
    and (optionally) an associated translation.
    """
    def __init__(self, line, translation=None, original=None):
        self.item = line
        self.translation = translation
        self.original = original
    
    def __str__(self):
        return self.item.to_srt() if self.item else None

    def __repr__(self):
        return f"Line({srt.timedelta_to_srt_timestamp(self.start) if self.start is not None else self.number}, {repr(self.text)})"

    @property
    def key(self):
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
        return srt.timedelta_to_srt_timestamp(self.start) if self.start is not None else None
    
    @property
    def end(self) -> timedelta:
        return self._item.end if self._item else None
    
    @property
    def srt_end(self) -> str:
        return srt.timedelta_to_srt_timestamp(self.end) if self.end else None
    
    @property
    def duration(self) -> timedelta:
        return self.end - self.start if self.start is not None and self.end else timedelta(seconds=0)

    @property
    def line(self):
        return self._item.to_srt() if self._item and self._item.content else None

    @property
    def translated(self):
        if not self._item or not self.translation:
            return None 
        return SubtitleLine.Construct(self.number, self.start, self.end, self.translation)

    @property
    def item(self):
        return self._item

    @classmethod
    def Construct(cls, number, start, end, text, original = None):
        number = int(number) if number else None
        start = GetTimeDelta(start)
        end = GetTimeDelta(end)
        text = srt.make_legal_content(text) if text else None
        original = srt.make_legal_content(original) if original else None
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

    @item.setter
    def item(self, item):
        if isinstance(item, SubtitleLine):
            item = item.item

        self._item = CreateSrtSubtitle(item)

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

    @end.setter
    def end(self, time):
        if self._item:
            self._item.end = GetTimeDelta(time)

    @classmethod
    def GetLines(lines):
        """
        (re)parse the lines, assuming SubRip format 
        """
        if all(isinstance(line, SubtitleLine) for line in lines):
            return lines
        else:
            return [SubtitleLine(line) for line in lines]

    @classmethod
    def GetLineItems(cls, lines, tag):
        """
        Generate a set of translation cues for the translator
        """
        items = SubtitleLine.GetLines(lines)
        return [ SubtitleLine.GetLineItem(item, tag) for item in items ]

    @classmethod
    def GetLineItem(cls, line, tag):
        """
        Format line for the translator
        """
        line = f"<{tag} line={line.number}>{line.text}</{tag}>"
        return line

    @classmethod
    def MergeSubtitles(cls, merged_lines):
        first_line = merged_lines[0]
        last_line = merged_lines[-1]
        merged_number = first_line.number 
        merged_start = first_line.start
        merged_end = last_line.end
        merged_content = "\n".join(line.text for line in merged_lines)
        subtitle = srt.Subtitle(merged_number, merged_start, merged_end, merged_content)
        return SubtitleLine(subtitle)

