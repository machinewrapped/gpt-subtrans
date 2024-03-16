from PySubtitle.Helpers import GenerateBatchPrompt, GenerateTagLines, WrapSystemMessage
from PySubtitle.SubtitleError import TranslationError

class TranslationPrompt:
    def __init__(self, user_prompt : str, conversation : bool, supports_system_prompt : bool, supports_system_messages : bool):
        self.conversation = conversation
        self.supports_system_prompt = supports_system_prompt
        self.supports_system_messages = supports_system_messages
        self.user_role = "user"
        self.assistant_role = "assistant"
        self.system_role = "system" if self.supports_system_messages else self.user_role
        self.system_prompt = None
        self.user_prompt = user_prompt
        self.batch_prompt = None
        self.content = None
        self.messages = []

    def GenerateMessages(self, instructions : str, lines : list, context : dict):
        """
        Generate the messages to request a translation
        """
        self.messages.clear()

        if context:
            tag_lines = GenerateTagLines(context, ['description', 'names', 'summaries', 'scene', 'summary', 'batch'])

            self.batch_prompt = GenerateBatchPrompt(self.user_prompt, lines, tag_lines)

        else:
            self.batch_prompt = GenerateBatchPrompt(self.user_prompt, lines)

        if instructions:
            if self.supports_system_prompt:
                self.system_prompt = instructions
                self.messages.append({'role': self.user_role, 'content': self.batch_prompt})
            elif self.supports_system_messages:
                self.messages.append({'role': self.system_role, 'content': instructions})
                self.messages.append({'role': self.user_role, 'content': self.batch_prompt})
            else:
                user_instructions = WrapSystemMessage(instructions)
                self.messages.append({'role': self.user_role, 'content': f"{user_instructions}\n{self.batch_prompt}"})
        else:
            self.messages.append({'role': self.user_role, 'content': self.batch_prompt})

        self._generate_content()

    def GenerateRetryPrompt(self, reponse : str, retry_instructions : str, errors : list[TranslationError]):
        """
        Request retranslation of lines that were not translated originally
        """
        messages = []
        for message in self.messages:
            messages.append(message)
            if message.get('role') == self.user_role:
                break

        messages.append({ 'role': self.assistant_role, 'content': reponse })

        if errors:
            unique_errors = set(( f"- {str(e).strip()}" for e in errors ))
            error_list = list(unique_errors)
            error_message = '\n'.join(error_list)
            retry_prompt = f"There were some problems with the translation:\n{error_message}\n\nPlease correct them."
        else:
            # Maybe less is more?
            retry_prompt = "There were some problems with the translation. Please try again."

        if self.supports_system_messages:
            messages.append({ 'role': self.system_role, 'content': retry_instructions })
        else:
            retry_prompt = f"{WrapSystemMessage(retry_instructions)}\n{retry_prompt}"

        messages.append({ 'role': self.user_role, 'content': retry_prompt })

        self.messages = messages
        self._generate_content()

    def _generate_content(self):
        self.content = self.messages if self.conversation else self._generation_completion()

    def _generation_completion(self):
        """ Convert a series of messages to a script for the AI to complete """
        return "\n\n".join([ f"#{m.get('role')} ###\n{m.get('content')}" for m in self.messages ])

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