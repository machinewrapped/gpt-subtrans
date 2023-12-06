from PySubtitle.Translation import Translation

class GPTTranslation(Translation):
    """ Wraps a translation response from the OpenAI Chat endpoint """
    @property
    def finish_reason(self):
        return self.response.get('finish_reason') if self.response else None

    @property
    def response_time(self):
        return self.response.get('response_time') if self.response else None

    @property
    def prompt_tokens(self):
        return self.response.get('prompt_tokens') if self.response else None

    @property
    def completion_tokens(self):
        return self.response.get('completion_tokens') if self.response else None

    @property
    def total_tokens(self):
        return self.response.get('total_tokens') if self.response else None

    @property
    def reached_token_limit(self):
        return self.finish_reason == "length"
    
    @property
    def quota_reached(self):
        return self.finish_reason == "quota_reached"
