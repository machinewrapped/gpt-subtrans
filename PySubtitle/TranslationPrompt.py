from typing import Optional, List

from PySubtitle.SubtitleError import TranslationError
from PySubtitle.SubtitleLine import SubtitleLine

default_prompt_template = "<context>\n{context}\n</context>\n\n{prompt}\n\n<summary>Summary of the batch</summary>\n<scene>Summary of the scene</scene>\n"
default_line_template = "#{number}\nOriginal>\n{text}\nTranslation>\n"
default_tag_template = "<{tag}>{content}</{tag}>"
default_context_tags = ['description', 'names', 'history', 'scene', 'summary', 'batch']

class TranslationPrompt:
    """
    Class for formatting a prompt to request translation of a batch of subtitles
    """
    def __init__(self, user_prompt : str, conversation : bool = True):
        """
        Construct a translation prompt for a batch of subtitles
        """
        # User prompt to include at the top of the prompt
        self.user_prompt = user_prompt

        # Flag controlling whether the prompt content is formatted as a list of messages for a conversational model
        self.conversation = conversation

        # Flag controlling whether to include a system prompt
        self.supports_system_prompt = False

        # Flag controlling whether to include messages in the "system" role
        self.supports_system_messages = False

        # Flag controlling whether to use the "system" role for retry instructions
        self.supports_system_messages_for_retry = False

        # Templates for formatting the prompt - override these to customize the prompt
        self.prompt_template = default_prompt_template
        self.line_template = default_line_template
        self.tag_template = default_tag_template
        self.context_tags = default_context_tags

        self.system_prompt = None
        self.batch_prompt = None
        self.content = None
        self.messages = []

    def GenerateMessages(self, instructions : str, lines : list, context : dict):
        """
        Generate the messages to request translation of a batch of subtitles

        :param instructions: instructions to provide to the translator
        :param lines: list of lines to translate
        :param context: dictionary of contextual information to include in the prompt
        """
        self.messages.clear()

        user_role = "user"
        system_role = "system" if self.supports_system_messages else user_role

        self.batch_prompt = self.GenerateBatchPrompt(lines, context=context)

        if not instructions:
            self.messages.append({'role': user_role, 'content': self.batch_prompt})
        elif self.supports_system_prompt:
            self.system_prompt = instructions
            self.messages.append({'role': user_role, 'content': self.batch_prompt})
        elif self.supports_system_messages:
            self.messages.append({'role': system_role, 'content': instructions})
            self.messages.append({'role': user_role, 'content': self.batch_prompt})
        else:
            user_instructions = self._wrap_system_message(instructions)
            self.messages.append({'role': user_role, 'content': f"{user_instructions}\n{self.batch_prompt}"})

        self._generate_content()

    def GenerateBatchPrompt(self, lines : list, context : dict = None):
        """
        Create the user prompt for translating a set of lines

        :param tag_lines: optional list of extra lines to include at the top of the prompt.
        :param template: optional template to format the prompt.
        """
        if not lines:
            raise ValueError("No source lines provided")

        source_lines = [ _get_line_prompt(line, self.line_template) for line in lines ]

        prompt = '\n\n'.join(source_lines).strip()

        if self.user_prompt:
            prompt = f"{self.user_prompt}\n\n{prompt}\n"

        tag_lines = _generate_tag_lines(context, self.context_tags, self.tag_template) if context else ""

        if tag_lines:
            prompt = self.prompt_template.format(prompt=prompt, context=tag_lines)

        return prompt

    def GenerateRetryPrompt(self, reponse : str, retry_instructions : str, errors : list[TranslationError]):
        """
        Request retranslation of lines that were not translated originally
        """
        messages = []

        user_role = "user"
        assistant_role = "assistant"
        system_role = "system" if self.supports_system_messages_for_retry else user_role

        for message in self.messages:
            messages.append(message)
            if message.get('role') == user_role:
                break

        messages.append({ 'role': assistant_role, 'content': reponse })

        if errors:
            unique_errors = set(( f"- {str(e).strip()}" for e in errors ))
            error_list = list(unique_errors)
            error_message = '\n'.join(error_list)
            retry_prompt = f"There were some problems with the translation:\n{error_message}\n\nPlease correct them."
        else:
            # Maybe less is more?
            retry_prompt = "There were some problems with the translation. Please try again."

        if self.supports_system_messages:
            messages.append({ 'role': system_role, 'content': retry_instructions })
        else:
            retry_prompt = f"{self._wrap_system_message(retry_instructions)}\n{retry_prompt}"

        messages.append({ 'role': user_role, 'content': retry_prompt })

        self.messages = messages
        self._generate_content()

    def _wrap_system_message(self, message : str):
        separator = "--------"
        return '\n'.join( [ separator, "SYSTEM", separator, message.strip(), separator])

    def _generate_content(self):
        self.content = self.messages if self.conversation else self._generate_completion()

    def _generate_completion(self):
        """ Convert a series of messages to a script for the AI to complete """
        if self.supports_system_messages:
            return "\n\n".join([ f"#{m.get('role')} ###\n{m.get('content')}" for m in self.messages ])
        else:
            return "\n\n".join([ m.get('content') for m in self.messages ])

def _get_line_prompt(line : SubtitleLine, line_template : str = None):
    """
    Generate a prompt for a single subtitle line
    """
    if not line._item:
        return None

    return line_template.format(number=line.number, text=line.text_normalized)

def _generate_tag(tag, content : str | List[str], tag_template : str) -> str:
    """
    Generate tag with content using the provided template
    """
    if isinstance(content, list):
        content = ', '.join(content)

    return tag_template.format(tag=tag, content=content).strip()

def _generate_tag_lines(context : dict, tags : List[str], tag_template : str) -> Optional[str]:
    """
    Create a user message for specifying a set of tags

    :param context: dictionary of tag, value pairs
    :param tags: list of tags to extract from the context.
    :param tag_template: template to use for each tag
    """
    tag_lines = [ _generate_tag(tag, context[tag], tag_template) for tag in tags if context.get(tag) ]

    if not tag_lines:
        return None

    return '\n'.join([ tag for tag in tag_lines if tag ])

