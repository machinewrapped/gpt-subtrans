from PySubtitle.Helpers import GenerateTagLines, ParseTranslation, PerformSubstitutions
from PySubtitle.TranslationPrompt import TranslationPrompt

class Translation:
    def __init__(self, content : dict):
        self.content = content
        translation_text = content.get('text')
        self._text, self.context = ParseTranslation(translation_text)

    def ParseResponse(self):
        pass

    @property
    def text(self):
        return self._text.strip() if self._text else None

    @property
    def has_translation(self):
        return True if self.text else False
        
    @property
    def summary(self):
        return self.context.get('summary')

    @property
    def scene(self):
        return self.context.get('scene')

    @property
    def synopsis(self):
        return self.context.get('synopsis')

    @property
    def names(self):
        return self.context.get('names')
    
    @property
    def finish_reason(self):
        return self.content.get('finish_reason')

    @property
    def response_time(self):
        return self.content.get('response_time')

    @property
    def reached_token_limit(self):
        return self.finish_reason == "length"
    
    @property
    def quota_reached(self):
        return self.finish_reason == "quota_reached"

    @property
    def full_text(self):
        tag_lines = GenerateTagLines(self.context, ['summary', 'scene', 'synopsis', 'names']) if self.context else None
        return f"{tag_lines}\n\n{self._text}" if tag_lines else self._text

    def PerformSubstitutions(self, substitutions, match_partial_words : bool = False):
        """
        Apply any text substitutions to summary, scene, names and synopsis if they exist.

        Does NOT apply them to the translation text. 
        """
        if self.summary:
            self.context['summary'] = PerformSubstitutions(substitutions, self.summary, match_partial_words)
        if self.scene:
            self.context['scene'] = PerformSubstitutions(substitutions, self.scene, match_partial_words)
        if self.synopsis:
            self.context['synopsis'] = PerformSubstitutions(substitutions, self.synopsis, match_partial_words)


