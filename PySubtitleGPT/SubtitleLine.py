from datetime import timedelta
from os import linesep
import srt

from PySubtitleGPT.Helpers import CreateSrtSubtitle, GetTimeDelta

class SubtitleLine:
    """
    Represents a single line, with a number and start and end times plus original text 
    and (optionally) an associated translation.
    """
    def __init__(self, line, translation=None):
        self.item = line
        self.translation = translation
    
    def __str__(self):
        return self.item.to_srt() if self.item else None

    def __repr__(self):
        return f"Line({srt.timedelta_to_srt_timestamp(self.start) if self.start else '***'}, {repr(self.text)})"

    @property
    def key(self):
        return str(self.start) if self.start else self.number

    @property
    def number(self):
        return self._item.index if self._item else None

    @property
    def text(self):
        return self._item.content if self._item else None

    @property
    def start(self) -> timedelta:
        return self._item.start if self._item else None
    
    @property
    def srt_start(self) -> str:
        return srt.timedelta_to_srt_timestamp(self._item.start) if self._item else None
    
    @property
    def end(self) -> timedelta:
        return self._item.end if self._item else None
    
    @property
    def srt_end(self) -> str:
        return srt.timedelta_to_srt_timestamp(self._item.end) if self._item else None
    
    @property
    def duration(self) -> timedelta:
        return self.end - self.start if self.start and self.end else timedelta(seconds=0)

    @property
    def line(self):
        return self._item.to_srt() if self._item else None

    @property
    def translated(self):
        if not self._item:
            return None 
        line = SubtitleLine(self._item)
        line.text = self.translation
        return line
    
    @property
    def prompt(self):
        if not self._item:
            return None
        
        return '\n'.join([
            f"<original start='{self.srt_start}' end='{self.srt_end}'>",
            self.text.replace(linesep, '\n'),
            f"</original>"
        ])

    @property
    def item(self):
        return self._item

    @classmethod
    def Construct(cls, number, start, end, text):
        start = GetTimeDelta(start)
        end = GetTimeDelta(end)
        text = srt.make_legal_content(text)
        item = srt.Subtitle(number, start, end, text)
        return SubtitleLine(item) 
    
    @classmethod
    def FromDictionary(cls, values):
        """
        Construct a SubtitleLine from a dictionary.
        """
        return SubtitleLine.Construct(
            values.get('number') or values.get('index'), 
            values['start'].strip(), 
            values['end'].strip(), 
            values['body'].strip())

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
            self._item.text = text

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
    def GetLineItems(lines, tag):
        """
        Generate a set of translation cues for the translator
        """
        items = SubtitleLine.GetLines(lines)
        return [ SubtitleLine.GetLineItem(item, tag) for item in items ]

    @classmethod
    def GetLineItem(line, tag):
        """
        Format line for the translator
        """
        line = f"<{tag} line={line.number}>{line.text}</{tag}>"
        return line

