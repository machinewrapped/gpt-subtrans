from PySubtitle.Helpers import GenerateBatchPrompt, GenerateTagLines
from PySubtitle.SubtitleError import TranslationError

class TranslationPrompt:
    def __init__(self, user_prompt : str, instructions : str, context : dict):
        self.user_prompt = user_prompt
        self.instructions = instructions
        self.context = context
        self.batch_prompt = None
        self.messages = []

    def GenerateMessages(self, lines):
        """
        Generate the messages to request a translation
        """
        if self.instructions:
            self.messages.append({'role': "system", 'content': self.instructions})

        if self.context:
            summaries = self.context.get('summaries')
            if summaries:
                self.messages.append({'role': "user", 'content': '\n'.join(summaries)})

            tag_lines = GenerateTagLines(self.context, ['description', 'names','scene', 'summary', 'batch'])

            self.batch_prompt = GenerateBatchPrompt(self.user_prompt, lines, tag_lines)

        else:
            self.batch_prompt = GenerateBatchPrompt(self.user_prompt, lines)

        self.messages.append({'role': "user", 'content': self.batch_prompt})

    def GenerateReducedMessages(self):
        """
        Remove context from the prompt to reduce the token count
        """
        self.messages.clear()
        if self.instructions:
            self.messages.append({'role': "system", 'content': self.instructions})
        
        self.messages.append({'role': "user", 'content': self.batch_prompt})

    def GenerateRetryPrompt(self, reponse : str, retry_instructions : str, errors : list[TranslationError]):
        """
        Request retranslation of lines that were not translated originally
        """
        messages = []
        for message in self.messages:
            if message.get('content') == retry_instructions:
                break
            messages.append(message)

        if errors:
            unique_errors = set(( f"- {str(e).strip()}" for e in errors ))
            error_list = list(unique_errors)
            error_message = '\n'.join(error_list)
            retry_prompt = f"There were some problems with the translation:\n{error_message}\n\nPlease correct them."
        else:
            # Maybe less is more?
            retry_prompt = 'Please try again'

        messages.extend([
            { 'role': "assistant", 'content': reponse },
            { 'role': "system", 'content': retry_instructions },
            { 'role': "user", 'content': retry_prompt }
        ])

        self.messages = messages

def FormatPrompt(prompt : TranslationPrompt):
    if prompt.batch_prompt:
        return prompt.batch_prompt
    else:
        lines = []

        if prompt.user_prompt:
            lines.append(f"User Prompt:\n {prompt.user_prompt}")
        
        if prompt.instructions:
            lines.append(f"Instructions:\n {prompt.instructions}")
    
        return "\n".join(lines)