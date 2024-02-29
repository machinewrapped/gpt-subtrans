import logging
import time

from PySubtitle.SubtitleError import TranslationAbortedError, TranslationError
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

    def RequestTranslation(self, prompt : str, lines : list, context : dict) -> Translation:
        """
        Generate the messages to request a translation
        """
        if self.aborted:
            raise TranslationAbortedError()

        start_time = time.monotonic()

        # Perform the translation
        translation : Translation = self._request_translation(prompt, lines, context)

        if translation.text:
            logging.debug(f"Response:\n{translation.text}")

        # If a rate limit is replied ensure a minimum duration for each request
        rate_limit = self.settings.get('rate_limit')
        if rate_limit and rate_limit > 0.0:
            minimum_duration = 60.0 / rate_limit

            elapsed_time = time.monotonic() - start_time
            if elapsed_time < minimum_duration:
                sleep_time = minimum_duration - elapsed_time
                time.sleep(sleep_time)

        return translation

    def RequestRetranslation(self, translation : Translation, errors : list[TranslationError]):
        """
        Generate the messages to request a retranslation
        """
        prompt = translation.prompt

        messages = []
        for message in prompt.messages:
            # Trim retry messages to keep tokens down
            if message.get('content') == self.retry_instructions:
                break
            messages.append(message)

        prompt.messages = messages

        prompt.GenerateRetryPrompt(translation.text, self.retry_instructions, errors)

        # Let's raise the temperature a little bit
        temperature = min(self.settings.get('temperature', 0.0) + 0.1, 1.0)
        retranslation_response = self._send_messages(prompt.messages, temperature)

        retranslation = Translation(retranslation_response, prompt)
        return retranslation
    
    def AbortTranslation(self):
        self.aborted = True
        self._abort()
        pass

    def _request_translation(self, prompt, lines, context):
        """
        Make a request to the API to provide a translation
        """
        raise NotImplementedError("Not implemented in the base class")

    def _send_messages(self, messages : list[str], temperature : float = None):
        """
        Communicate with the API
        """
        raise NotImplementedError("Not implemented in the base class")

    def _abort(self):
        # Try to terminate ongoing requests
        pass
