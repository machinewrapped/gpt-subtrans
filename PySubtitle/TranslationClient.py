import logging
import time

from PySubtitle.Instructions import DEFAULT_TASK_TYPE
from PySubtitle.SubtitleError import TranslationError
from PySubtitle.TranslationParser import TranslationParser
from PySubtitle.TranslationPrompt import TranslationPrompt, default_prompt_template
from PySubtitle.Translation import Translation

linesep = '\n'

class TranslationClient:
    """
    Handles communication with the translation provider
    """
    def __init__(self, settings : dict):
        self.settings = settings
        self.instructions = settings.get('instructions')
        self.retry_instructions = settings.get('retry_instructions')
        self.aborted = False

        if not self.instructions:
            raise TranslationError("No instructions provided for the translator")

    @property
    def supports_conversation(self):
        return self.settings.get('supports_conversation', False)

    @property
    def supports_system_prompt(self):
        return self.settings.get('supports_system_prompt', False)

    @property
    def supports_system_messages(self):
        return self.settings.get('supports_system_messages', False)

    @property
    def supports_system_messages_for_retry(self):
        return self.settings.get('supports_system_messages_for_retry', self.supports_system_messages)

    @property
    def prompt_template(self):
        return self.settings.get('prompt_template') or default_prompt_template

    @property
    def rate_limit(self):
        return self.settings.get('rate_limit')

    @property
    def temperature(self):
        return self.settings.get('temperature', 0.0)

    @property
    def max_retries(self):
        return self.settings.get('max_retries', 3.0)

    @property
    def backoff_time(self):
        return self.settings.get('backoff_time', 5.0)

    def BuildTranslationPrompt(self, user_prompt : str, instructions : str, lines : list, context : dict):
        """
        Generate a translation prompt for the context
        """
        prompt = TranslationPrompt(user_prompt, self.supports_conversation)
        prompt.supports_system_prompt = self.supports_system_prompt
        prompt.supports_system_messages = self.supports_conversation and self.supports_system_messages
        prompt.supports_system_messages_for_retry = self.supports_system_messages_for_retry
        prompt.prompt_template = self.prompt_template
        prompt.GenerateMessages(instructions, lines, context)
        return prompt

    def RequestTranslation(self, prompt : TranslationPrompt, temperature : float = None) -> Translation:
        """
        Generate the messages to request a translation
        """
        start_time = time.monotonic()

        # Perform the translation
        translation : Translation = self._request_translation(prompt, temperature)

        if self.aborted or translation is None:
            return None

        if translation.text:
            logging.debug(f"Response:\n{translation.text}")

        # If a rate limit is replied ensure a minimum duration for each request
        rate_limit = self.rate_limit
        if rate_limit and rate_limit > 0.0:
            minimum_duration = 60.0 / rate_limit

            elapsed_time = time.monotonic() - start_time
            if elapsed_time < minimum_duration:
                sleep_time = minimum_duration - elapsed_time
                logging.debug(f"Sleeping for {sleep_time:.2f} seconds to respect rate limit")
                time.sleep(sleep_time)

        return translation

    def GetParser(self, task_type = DEFAULT_TASK_TYPE) -> TranslationParser:
        """
        Return a parser that can process the provider's response
        """
        return TranslationParser(task_type, self.settings)

    def AbortTranslation(self):
        self.aborted = True
        self._abort()
        pass

    def _request_translation(self, prompt : TranslationPrompt, temperature : float = None) -> Translation:
        """
        Make a request to the API to provide a translation
        """
        raise NotImplementedError

    def _abort(self):
        # Try to terminate ongoing requests
        pass
