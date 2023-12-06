import logging
import time

from PySubtitle.Options import Options
from PySubtitle.SubtitleError import TranslationError
from PySubtitle.Translation import Translation

linesep = '\n'

class TranslationClient:
    """
    Handles communication with OpenAI to request translations
    """
    def __init__(self, options : Options, instructions=None):
        self.options = options
        self.instructions = instructions or options.get('instructions', "")

        if not self.instructions:
            raise TranslationError("No instructions provided for the translator")

    def RequestTranslation(self, prompt : str, lines : list, context : dict) -> Translation:
        """
        Generate the messages to request a translation
        """
        options = self.options

        start_time = time.monotonic()

        # Perform the translation
        translation : Translation = self._request_translation(prompt, lines, context)

        if translation.text:
            logging.debug(f"Response:\n{translation.text}")

        # If a rate limit is replied ensure a minimum duration for each request
        rate_limit = options.get('rate_limit')
        if rate_limit and rate_limit > 0.0:
            minimum_duration = 60.0 / rate_limit

            elapsed_time = time.monotonic() - start_time
            if elapsed_time < minimum_duration:
                sleep_time = minimum_duration - elapsed_time
                time.sleep(sleep_time)

        return translation

    def RequestRetranslation(self, translation : Translation, errors : list[TranslationError]):
        """
        Generate the messages to send to OpenAI to request a retranslation
        """
        options = self.options
        prompt = translation.prompt

        retry_instructions = options.get('retry_instructions')

        if not retry_instructions:
            logging.warning("No retry instructions found, using defaults")
            retry_instructions = Options().get('retry_instructions') or "Try again"

        messages = []
        for message in prompt.messages:
            # Trim retry messages to keep tokens down
            if message.get('content') == retry_instructions:
                break
            messages.append(message)

        prompt.messages = messages

        prompt.GenerateRetryPrompt(translation.text, retry_instructions, errors)

        # Let's raise the temperature a little bit
        temperature = min(options.get('temperature', 0.0) + 0.1, 1.0)
        retranslation_response = self._send_messages(prompt.messages, temperature)

        retranslation = Translation(retranslation_response, prompt)
        return retranslation

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

