import logging
import time
import openai

from PySubtitle.Helpers import ParseDelayFromHeader
from PySubtitle.Providers.OpenAI.OpenAIClient import OpenAIClient
from PySubtitle.SubtitleError import NoTranslationError, TranslationAbortedError, TranslationImpossibleError

linesep = '\n'

class ChatGPTClient(OpenAIClient):
    """
    Handles chat communication with OpenAI to request translations
    """
    def __init__(self, settings : dict):
        settings['supports_system_messages'] = True
        settings['supports_conversation'] = True
        super().__init__(settings)

    def SupportedModels(self, available_models : list[str]):
        return [ model for model in available_models if model.find("instruct") < 0]

    def _send_messages(self, messages : list[str], temperature):
        """
        Make a request to the OpenAI API to provide a translation
        """
        response = {}

        for retry in range(self.max_retries):
            if self.aborted:
                raise TranslationAbortedError()

            try:
                result = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature 
                )

                if self.aborted:
                    raise TranslationAbortedError()

                response['response_time'] = getattr(result, 'response_ms', 0)

                if result.usage:
                    response['prompt_tokens'] = getattr(result.usage, 'prompt_tokens')
                    response['output_tokens'] = getattr(result.usage, 'completion_tokens')
                    response['total_tokens'] = getattr(result.usage, 'total_tokens')

                # We only expect one choice to be returned as we have 0 temperature
                if result.choices:
                    choice = result.choices[0]
                    reply = result.choices[0].message

                    response['finish_reason'] = getattr(choice, 'finish_reason', None)
                    response['text'] = getattr(reply, 'content', None)
                else:
                    raise NoTranslationError("No choices returned in the response", result)

                # Return the response if the API call succeeds
                return response
            
            except openai.RateLimitError as e:
                retry_after = e.response.headers.get('x-ratelimit-reset-requests') or e.response.headers.get('Retry-After')
                if retry_after:
                    retry_seconds = ParseDelayFromHeader(retry_after)
                    logging.warning(f"Rate limit hit, retrying in {retry_seconds} seconds...")
                    time.sleep(retry_seconds)
                    continue
                else:
                    raise TranslationImpossibleError("OpenAI account quota reached, please upgrade your plan", response)

            except openai.APITimeoutError as e:
                if self.aborted:
                    raise TranslationAbortedError()

                sleep_time = self.backoff_time * 2.0**retry
                logging.warning(f"OpenAI error {str(e)}, retrying in {sleep_time}...")
                time.sleep(sleep_time)
                continue

            except openai.APIConnectionError as e:
                raise TranslationAbortedError() if self.aborted else TranslationImpossibleError(str(e), response)

            except Exception as e:
                raise TranslationImpossibleError(f"Unexpected error communicating with OpenAI", response, error=e)

        return None

