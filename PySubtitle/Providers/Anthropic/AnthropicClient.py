import logging
import time
import anthropic

from PySubtitle.Helpers import FormatMessages, ParseDelayFromHeader
from PySubtitle.SubtitleError import NoTranslationError, TranslationAbortedError, TranslationFailedError, TranslationImpossibleError
from PySubtitle.TranslationClient import TranslationClient
from PySubtitle.Translation import Translation
from PySubtitle.TranslationClient import TranslationClient
from PySubtitle.TranslationParser import TranslationParser
from PySubtitle.TranslationPrompt import TranslationPrompt

linesep = '\n'

class AnthropicClient(TranslationClient):
    """
    Handles communication with Claude via the anthropic SDK
    """
    def __init__(self, settings : dict):
        super().__init__(settings)

        logging.info(f"Translating with Anthropic {self.model or 'default model'}")

        try:
            self.client = anthropic.Anthropic(api_key=self.api_key)

        except Exception as e:
            logging.error(f"Failed to initialize Anthropic client: {e}")

    @property
    def api_key(self):
        return self.settings.get('api_key')

    @property
    def model(self):
        return self.settings.get('model')
    
    @property
    def max_tokens(self):
        return self.settings.get('max_tokens', 0)
    
    def _request_translation(self, prompt : TranslationPrompt, temperature : float = None) -> Translation:
        """
        Request a translation based on the provided prompt
        """
        logging.debug(f"Messages:\n{FormatMessages(prompt.messages)}")

        temperature = temperature or self.temperature
        response = self._send_messages(prompt.system_prompt, prompt.content, temperature)

        translation = Translation(response)

        if translation.quota_reached:
            raise TranslationImpossibleError("OpenAI account quota reached, please upgrade your plan or wait until it renews", translation)

        if translation.reached_token_limit:
            raise TranslationFailedError(f"Too many tokens in translation", translation)

        return translation

    def GetParser(self):
        return TranslationParser(self.settings)    

    def _send_messages(self, system_prompt : str, messages : list[str], temperature):
        """
        Make a request to the LLM to provide a translation
        """
        response = {}

        for retry in range(self.max_retries):
            if self.aborted:
                raise TranslationAbortedError()

            try:
                result = self.client.messages.create(
                    model=self.model,
                    messages=messages,
                    system=system_prompt,
                    temperature=temperature,
                    max_tokens=self.max_tokens
                )

                if self.aborted:
                    raise TranslationAbortedError()

                if not result.content:
                    raise NoTranslationError("No choices returned in the response", result)

                # response['response_time'] = getattr(response, 'response_ms', 0)

                if result.stop_reason == 'max_tokens':
                    response['finish_reason'] = "length"
                else:
                    response['finish_reason'] = result.stop_reason
                
                if result.usage:
                    response['prompt_tokens'] = getattr(result.usage, 'input_tokens')
                    response['output_tokens'] = getattr(result.usage, 'output_tokens')

                for piece in result.content:
                    if piece.type == 'text':
                        response['text'] = piece.text
                        break

                # Return the response if the API call succeeds
                return response
            
            except (anthropic.APITimeoutError, anthropic.RateLimitError) as e:
                if self.aborted:
                    raise TranslationAbortedError()

                sleep_time = self.backoff_time * 2.0**retry
                logging.warning(f"Provider error {str(e)}, retrying in {sleep_time}...")
                time.sleep(sleep_time)
                continue

            except Exception as e:
                raise TranslationImpossibleError(f"Unexpected error communicating with provider", response, error=e)

        return None

