from os import linesep
from pysrt import SubRipItem

from PySubtitleGPT.Helpers import FixTime

class Subtitle:
    """
    Represents a single subtitle line, with an index and start and end times plus original text 
    and (optionally) an associated translation.
    """
    def __init__(self, line, translation=None):
        self.item = line
        self.translation = translation
    
    def __str__(self):
        return str(self.item)

    def __repr__(self):
        return f"Subtitle({str(self.key)}, {repr(self.text)})"

    @property
    def key(self):
        return str(self.start) if self.start else self.index

    @property
    def index(self):
        return self._item.index if self._item else None

    @property
    def text(self):
        return self._item.text_without_tags if self._item else None

    @property
    def start(self):
        return self._item.start if self._item else None
    
    @property
    def end(self):
        return self._item.end if self._item else None

    @property
    def line(self):
        return str(self._item) if self._item else None

    @property
    def translated(self):
        if not self._item:
            return None 
        subtitle = Subtitle(self._item)
        subtitle.text = self.translation
        return subtitle
    
    @property
    def prompt(self):
        if not self._item:
            return None
        
        return '\n'.join([
            f"<original start='{self.start}' end='{self.end}'>",
            self.text.replace(linesep, '\n'),
            f"</original>"
        ])

    @property
    def item(self):
        return self._item

    @classmethod
    def Construct(cls, index, start, end, text):
        start = FixTime(start)
        end = FixTime(end)
        item = SubRipItem(index, start, end, text)
        return Subtitle(item) 
    
    @classmethod
    def FromDictionary(cls, values):
        """
        Construct a Subtitle from a dictionary.
        """
        return Subtitle.Construct(values.get('index'), values['start'].strip(), values['end'].strip(), values['body'].strip())

    @classmethod
    def FromMatch(cls, match):
        """
        Construct a Subtitle from a regex match.

        Really should use named groups, but findall doesn't seem to preserve the names. 
        """
        if len(match) > 3:
            index, start, end, body = match
        else:
            start, end, body = match
            index = None
            
        return Subtitle.Construct(index, start.strip(), end.strip(), body.strip())

    @item.setter
    def item(self, item):
        self._item = SubRipItem.from_lines(str(item).strip().split('\n'))

    @index.setter
    def index(self, index):
        if self._item:
            self._item.index = index

    @text.setter
    def text(self, text):
        if self._item:
            self._item.text = text

    @start.setter
    def start(self, time):
        if self._item:
            self._item.start = SubRipItem.coerce(time)

    @end.setter
    def end(self, time):
        if self._item:
            self._item.end = SubRipItem.coerce(time)

    @classmethod
    def GetSubtitles(lines):
        """
        (re)parse the lines as subtitles, assuming SubRip format 
        """
        if all(isinstance(line, Subtitle) for line in lines):
            return lines
        else:
            return [Subtitle(line) for line in lines]

    @classmethod
    def GetLineItems(lines, tag):
        """
        Generate a set of translation lines for the translator
        """
        items = Subtitle.GetSubtitles(lines)
        return [Subtitle.GetLineItem(item, tag) for item in items]

    @classmethod
    def GetLineItem(item, tag):
        """
        Generate the translation prompt line for a subtitle
        """
        line = f"<{tag} line={item.index}>{item.text}</{tag}>"
        return line

