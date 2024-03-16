import logging
import openai
import time
from PySubtitle.Helpers import ParseDelayFromHeader
from PySubtitle.Helpers import FormatMessages
from PySubtitle.SubtitleError import TranslationError, TranslationImpossibleError
from PySubtitle.Translation import Translation
from PySubtitle.TranslationClient import TranslationClient
from PySubtitle.TranslationParser import TranslationParser
from PySubtitle.TranslationPrompt import TranslationPrompt
from PySubtitle.SubtitleError import NoTranslationError, TranslationAbortedError, TranslationImpossibleError

class AzureOpenAIClient(TranslationClient):
    """
    Handles communication with AzureOpenAI to request translations
    """
    def __init__(self, settings : dict):
        super().__init__(settings)

        if not hasattr(openai, "AzureOpenAI"):
            raise Exception("The OpenAI library is out of date and must be updated")

        if not self.api_key:
            raise ValueError('API key must be set in .env or provided as an argument')

        logging.info(f"Translating with Azure OpenAI deployment {self.deployment_name}, API-version {self.api_version}, API Base: {self.api_base}")

        self.client = openai.AzureOpenAI(azure_endpoint=self.api_base, api_version=self.api_version, azure_deployment=self.deployment_name, api_key=self.api_key)

    @property
    def api_key(self):
        return self.settings.get('api_key')

    @property
    def api_base(self):
        return self.settings.get('api_base')

    @property
    def api_version(self):
        return self.settings.get('api_version')

    @property
    def deployment_name(self):
        return self.settings.get('deployment_name')

    @property
    def rate_limit(self):
        return self.settings.get('rate_limit')

    def _request_translation(self, prompt : TranslationPrompt, temperature : float = None) -> Translation:
        """
        Request a translation based on the provided prompt
        """
        logging.debug(f"Messages:\n{FormatMessages(prompt.messages)}")

        temperature = temperature or self.temperature
        content = self._send_messages(prompt.messages, temperature)

        translation = Translation(content)

        return translation

    def _send_messages(self, messages : list[str], temperature):
        """
        Make a request to the Azure OpenAI API to provide a translation
        """
        content = {}

        for retry in range(self.max_retries):
            if self.aborted:
                raise TranslationAbortedError()

            try:
                response = self.client.chat.completions.create(
                    model=self.deployment_name,
                    messages=messages,
                    temperature=temperature
                )

                if self.aborted:
                    raise TranslationAbortedError()

                content['response_time'] = getattr(response, 'response_ms', 0)

                if response.usage:
                    content['prompt_tokens'] = getattr(response.usage, 'prompt_tokens')
                    content['completion_tokens'] = getattr(response.usage, 'completion_tokens')
                    content['total_tokens'] = getattr(response.usage, 'total_tokens')

                # We only expect one choice to be returned as we have 0 temperature
                if response.choices:
                    choice = response.choices[0]
                    reply = response.choices[0].message

                    content['finish_reason'] = getattr(choice, 'finish_reason', None)
                    content['text'] = getattr(reply, 'content', None)
                else:
                    raise NoTranslationError("No choices returned in the response", response)

                # Return the response if the API call succeeds
                return content

            except openai.RateLimitError as e:
                retry_after = e.response.headers.get('x-ratelimit-reset-requests') or e.response.headers.get('Retry-After')
                if retry_after:
                    retry_seconds = ParseDelayFromHeader(retry_after)
                    logging.warning(f"Rate limit hit, retrying in {retry_seconds} seconds...")
                    time.sleep(retry_seconds)
                    continue
                else:
                    raise TranslationImpossibleError("OpenAI account quota reached, please upgrade your plan", content)

            except openai.APITimeoutError as e:
                if self.aborted:
                    raise TranslationAbortedError()

                sleep_time = self.backoff_time * 2.0**retry
                logging.warning(f"OpenAI error {str(e)}, retrying in {sleep_time}...")
                time.sleep(sleep_time)
                continue

            except openai.APIConnectionError as e:
                raise TranslationAbortedError() if self.aborted else TranslationImpossibleError(str(e), content)

            except Exception as e:
                raise TranslationImpossibleError(f"Unexpected error communicating with OpenAI", content, error=e)

        return None

    def _abort(self):
        self.client.close()
        return super()._abort()

    def GetParser(self):
        return TranslationParser(self.settings)