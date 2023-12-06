from PySubtitle.TranslationPrompt import TranslationPrompt
from PySubtitle.Helpers import GenerateTagLines, ParseTranslation, PerformSubstitutions

class Translation:
    def __init__(self, response, prompt : TranslationPrompt):
        self.prompt = prompt
        self.response = response
        self._text = response.get('text') if response else None
        self.context = None

    def ParseResponse(self):
        self._text, self.context = ParseTranslation(self.full_text or "")

    @property
    def text(self):
        return self._text.strip() if self._text else None

    @property
    def has_translation(self):
        return self.text
        
    @property
    def user_prompt(self):
        return self.prompt.user_prompt if self.prompt else None
    
    @property
    def summary(self):
        return self.context.get('summary') if self.context else None

    @property
    def scene(self):
        return self.context.get('scene') if self.context else None

    @property
    def synopsis(self):
        return self.context.get('synopsis') if self.context else None

    @property
    def characters(self):
        return self.context.get('characters') if self.context else None
    
    @property
    def full_text(self):
        tag_lines = GenerateTagLines(self.context, ['summary', 'scene', 'synopsis', 'characters']) if self.context else None
        return f"{tag_lines}\n\n{self._text}" if tag_lines else self._text

    def PerformSubstitutions(self, substitutions, match_partial_words : bool = False):
        """
        Apply any text substitutions to summary, scene, characters and synopsis if they exist.

        Does NOT apply them to the translation text. 
        """
        if self.summary:
            self.context['summary'] = PerformSubstitutions(substitutions, self.summary, match_partial_words)
        if self.scene:
            self.context['scene'] = PerformSubstitutions(substitutions, self.scene, match_partial_words)
        if self.characters:
            self.context['characters'], _ = PerformSubstitutions(substitutions, self.characters, match_partial_words)
        if self.synopsis:
            self.context['synopsis'] = PerformSubstitutions(substitutions, self.synopsis, match_partial_words)


