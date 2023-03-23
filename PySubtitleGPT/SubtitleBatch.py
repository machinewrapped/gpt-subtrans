from PySubtitleGPT.Helpers import PerformSubstitutions
from PySubtitleGPT.Subtitle import Subtitle

class SubtitleBatch:
    def __init__(self, dict = None):
        dict = dict or {}
        self.number = dict.get('number')
        self.summary = dict.get('summary')
        self.context = dict.get('context', {})
        self.translation = dict.get('translation')
        self._subtitles = dict.get('subtitles', [])
        self._translated = dict.get('translated', [])

    @property
    def subtitles(self):
        return self._subtitles
    
    @property
    def size(self):
        return len(self._subtitles)
    
    @property
    def translated(self):
        return self._translated

    @property
    def untranslated(self):
        return [sub for sub in self.subtitles if not sub.translation]

    @property
    def all_translated(self):
        return all(sub.translation for sub in self.subtitles)

    @translated.setter
    def translated(self, value):
        self._translated = [ Subtitle(line) for line in value ]

    def AddLine(self, line):
        self._subtitles.append(Subtitle(line))

    def AddTranslation(self, line):
        self._translated.append(Subtitle(line))

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
        if self.subtitles:
            lines = [item.text for item in self.subtitles]

            lines, replacements = PerformSubstitutions(substitutions, lines)

            if replacements:
                self.AddContext('input_replacements', replacements)
                for item in self.subtitles:
                    item.text = replacements.get(item.text) or item.text

            return replacements

    def PerformOutputSubstitutions(self, substitutions):
        """
        Perform any word/phrase substitutions on translated text
        """
        if self.translated:
            lines = [item.text for item in self.translated]

            translated, replacements = PerformSubstitutions(substitutions, lines)

            if replacements:
                self.AddContext('output_replacements', replacements)
                for item in self.translated:
                    item.text = replacements.get(item.text) or item.text

            return replacements

