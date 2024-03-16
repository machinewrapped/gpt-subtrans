from PySubtitle.Helpers import GenerateTagLines, ParseTranslation, PerformSubstitutions
from PySubtitle.TranslationPrompt import TranslationPrompt

class Translation:
    def __init__(self, content : dict):
        self.content = content
        translation_text = content.get('text')
        self._text, context = ParseTranslation(translation_text)
        self.content.update(context)

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
        return self.content.get('summary')

    @property
    def scene(self):
        return self.content.get('scene')

    @property
    def synopsis(self):
        return self.content.get('synopsis')

    @property
    def names(self):
        return self.content.get('names')
    
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
        return self.content.get('text', self._text)

    def PerformSubstitutions(self, substitutions, match_partial_words : bool = False):
        """
        Apply any text substitutions to summary, scene, names and synopsis if they exist.

        Does NOT apply them to the translation text. 
        """
        if self.summary:
            self.content['summary'] = PerformSubstitutions(substitutions, self.summary, match_partial_words)
        if self.scene:
            self.content['scene'] = PerformSubstitutions(substitutions, self.scene, match_partial_words)
        if self.synopsis:
            self.content['synopsis'] = PerformSubstitutions(substitutions, self.synopsis, match_partial_words)

    def FormatResponse(self, include_text : bool = True):
        """
        Format the response for display
        """
        if not self.content:
            return "No translation"

        content_keys = [k for k in self.content.keys() if k not in ['text', 'summary', 'scene', 'names']]
        metadata = [ f"{k}: {self.content[k]}" for k in content_keys if self.content.get(k) ]

        if self.scene:
            metadata.append(f"\nScene:\n{self.scene}")

        if self.summary:
            metadata.append(f"\nSummary:\n{self.summary}")

        if self.names:
            names = "\n".join(self.names)
            metadata.append(f"\n\nNames:\n{names}")

        if metadata:
            metadata_text = '\n'.join(metadata)
            return f"{metadata_text}\n\n{self.text}" if include_text else metadata_text
        else:
            return self.text if include_text else "No metadata available"
            


