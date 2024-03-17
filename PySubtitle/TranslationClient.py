import logging
import time

from PySubtitle.SubtitleError import TranslationAbortedError, TranslationError
from PySubtitle.TranslationPrompt import TranslationPrompt
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

    def RequestTranslation(self, prompt : TranslationPrompt, temperature : float = None) -> Translation:
        """
        Generate the messages to request a translation
        """
        if self.aborted:
            raise TranslationAbortedError()

        start_time = time.monotonic()

        # Perform the translation
        translation : Translation = self._request_translation(prompt, temperature)

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

    def AbortTranslation(self):
        self.aborted = True
        self._abort()
        pass

    def _request_translation(self, prompt : TranslationPrompt, temperature : float = None) -> Translation:
        """
        Make a request to the API to provide a translation
        """
        raise NotImplementedError("Not implemented in the base class")

    def _abort(self):
        # Try to terminate ongoing requests
        pass
