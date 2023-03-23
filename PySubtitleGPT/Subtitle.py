from os import linesep
from pysrt import SubRipItem

class Subtitle:
    """
    Represents a single subtitle line, with an index and start and end times plus original text and translated text.
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
    def construct(cls, index, start, end, text):
        item = SubRipItem(index, start, end, text)
        return Subtitle(item) 

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

