from PySubtitle.SubtitleError import TranslationError

class TranslationPrompt:
    def __init__(self, instructions):
        self.user_prompt = None
        self.messages = []
        self.instructions = instructions
        
    def GenerateMessages(self, prompt, lines, context):
        raise NotImplementedError("Not implemented in the base class")

    def GenerateRetryPrompt(self, reponse : str, retry_instructions : str, errors : list[TranslationError]):
        raise NotImplementedError("Not implemented in the base class")


