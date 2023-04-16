from PySubtitleGPT.ChatGPTPrompt import ChatGPTPrompt
from PySubtitleGPT.Helpers import ParseTranslation, PerformSubstitutions

class ChatGPTTranslation:
    def __init__(self, response, prompt : ChatGPTPrompt):
        self.prompt = prompt
        self._text = response.get('text') if response else None
        self.finish_reason = response.get('finish_reason') if response else None
        self.response_time = response.get('response_time') if response else None
        self.prompt_tokens = response.get('prompt_tokens') if response else None
        self.completion_tokens = response.get('completion_tokens') if response else None
        self.total_tokens = response.get('total_tokens') if response else None

        self._text, self.summary, self.synopsis, self.characters = ParseTranslation(self.text or "")

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
    def reached_token_limit(self):
        return self.finish_reason == "length"
    
    @property
    def quota_reached(self):
        return self.finish_reason == "quota_reached"

    def PerformSubstitutions(self, substitutions):
        """
        Apply any text substitutions to summary, characters and synopsis if they exist.

        Does NOT apply them to the translation text. 
        """
        if self.summary:
            self.summary = PerformSubstitutions(substitutions, self.summary)
        if self.characters:
            self.characters, _ = PerformSubstitutions(substitutions, self.characters)
        if self.synopsis:
            self.synopsis = PerformSubstitutions(substitutions, self.synopsis)


