from PySubtitle.Helpers import GenerateTagLines, ParseTranslation, PerformSubstitutions
from PySubtitle.Translation import Translation

class ChatGPTTranslation(Translation):
    def __init__(self, response, prompt):
        super().__init__(response, prompt)
        self.finish_reason = response.get('finish_reason') if response else None
        self.response_time = response.get('response_time') if response else None
        self.prompt_tokens = response.get('prompt_tokens') if response else None
        self.completion_tokens = response.get('completion_tokens') if response else None
        self.total_tokens = response.get('total_tokens') if response else None

    @property
    def reached_token_limit(self):
        return self.finish_reason == "length"
    
    @property
    def quota_reached(self):
        return self.finish_reason == "quota_reached"
