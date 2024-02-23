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
    def SupportedModels(self, available_models : list[str]):
        return [ model for model in available_models if model.find("instruct") < 0]

    def _send_messages(self, messages : list[str], temperature : float = None):
        """
        Make a request to the OpenAI API to provide a translation
        """
        translation = {}
        retries = 0

        while retries <= self.max_retries and not self.aborted:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature
                )

                if self.aborted:
                    raise TranslationAbortedError()

                translation['response_time'] = getattr(response, 'response_ms', 0)

                if response.usage:
                    translation['prompt_tokens'] = getattr(response.usage, 'prompt_tokens')
                    translation['completion_tokens'] = getattr(response.usage, 'completion_tokens')
                    translation['total_tokens'] = getattr(response.usage, 'total_tokens')

                # We only expect one choice to be returned as we have 0 temperature
                if response.choices:
                    choice = response.choices[0]
                    reply = response.choices[0].message

                    translation['finish_reason'] = getattr(choice, 'finish_reason', None)
                    translation['text'] = getattr(reply, 'content', None)
                else:
                    raise NoTranslationError("No choices returned in the response", response)

                # Return the response if the API call succeeds
                return translation
            
            except openai.RateLimitError as e:
                retry_after = e.response.headers.get('x-ratelimit-reset-requests') or e.response.headers.get('Retry-After')
                if retry_after:
                    retry_seconds = ParseDelayFromHeader(retry_after)
                    logging.warning(f"Rate limit hit, retrying in {retry_seconds} seconds...")
                    time.sleep(retry_seconds)
                    continue
                else:
                    logging.warning("Rate limit hit, quota exceeded. Please wait until the quota resets.")
                    raise

            except (openai.APIConnectionError, openai.APITimeoutError) as e:
                if self.aborted:
                    raise TranslationAbortedError()
                
                if isinstance(e, openai.APIConnectionError):
                    raise TranslationImpossibleError(str(e), translation)
                elif retries == self.max_retries:
                    logging.warning(f"OpenAI failure {str(e)}, aborting after {retries} retries...")
                    raise
                else:
                    retries += 1
                    sleep_time = self.backoff_time * 2.0**retries
                    logging.warning(f"OpenAI error {str(e)}, retrying in {sleep_time}...")
                    time.sleep(sleep_time)
                    continue

            except Exception as e:
                raise TranslationImpossibleError(f"Unexpected error communicating with OpenAI", translation, error=e)

        return None

