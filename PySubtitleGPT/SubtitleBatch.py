from datetime import timedelta
from PySubtitleGPT.Helpers import PerformSubstitutions
from PySubtitleGPT.SubtitleLine import SubtitleLine

class SubtitleBatch:
    def __init__(self, dct = None):
        dct = dct or {}
        self.scene = dct.get('scene', None)
        self.number = dct.get('batch') or dct.get('number')
        self.summary = dct.get('summary')
        self.context = dct.get('context', {})
        self.translation = dct.get('translation')
        self.errors = dct.get('errors', [])
        self._originals = dct.get('originals', []) or dct.get('subtitles', []) 
        self._translated = dct.get('translated', [])

    def __str__(self) -> str:
        return f"SubtitleBatch: {str(self.number)} in scene {str(self.scene)} with {self.size} lines"

    def __repr__(self) -> str:
        return str(self)

    @property
    def originals(self) -> list[SubtitleLine]:
        return self._originals
    
    @property
    def size(self):
        return len(self._originals)
    
    @property
    def translated(self) -> list[SubtitleLine]:
        return self._translated

    @property
    def untranslated(self):
        return [sub for sub in self.originals if not sub.translated]

    @property
    def all_translated(self):
        return self.translated and (len(self.translated) == len(self.originals))
    
    @property
    def start(self) -> timedelta:
        return self.originals[0].start if self.originals else None
        
    @property
    def end(self) -> timedelta:
        return self.originals[-1].end if self.originals else None
    
    @property
    def duration(self):
        return self.end - self.start if self.start and self.end else timedelta(seconds=0)
    
    @originals.setter
    def originals(self, value):
        self._originals = [ SubtitleLine(line) for line in value ] if value else None

    @translated.setter
    def translated(self, value):
        self._translated = [ SubtitleLine(line) for line in value ] if value else None

    def AddLine(self, line):
        self._originals.append(SubtitleLine(line))

    def AddTranslatedLine(self, line):
        self._translated.append(SubtitleLine(line))

    def AddContext(self, key, value):
        self.context[key] = value

    def GetContext(self, key):
        return self.context.get(key)
    
    def SetContext(self, context):
        self.context = context.copy()

    def PerformInputSubstitutions(self, substitutions):
        """
        Perform any word/phrase substitutions on source text
        """
        if substitutions and self.originals:
            lines = [item.text for item in self.originals]

            lines, replacements = PerformSubstitutions(substitutions, lines)

            if replacements:
                self.AddContext('input_replacements', replacements)
                for item in self.originals:
                    item.text = replacements.get(item.text) or item.text

            return replacements

    def PerformOutputSubstitutions(self, substitutions):
        """
        Perform any word/phrase substitutions on translated text
        """
        if substitutions and self.translated:
            lines = [item.text for item in self.translated]

            _, replacements = PerformSubstitutions(substitutions, lines)

            if replacements:
                self.AddContext('output_replacements', replacements)
                for item in self.translated:
                    item.text = replacements.get(item.text) or item.text

            return replacements

