import logging
import time
import openai
from openai.types.chat import ChatCompletion

from PySubtitle.Helpers import ParseDelayFromHeader
from PySubtitle.Providers.OpenAI.OpenAIClient import OpenAIClient
from PySubtitle.SubtitleError import TranslationError, TranslationImpossibleError, TranslationResponseError

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

        for retry in range(self.max_retries + 1):
            if self.aborted:
                return None

            try:
                result : ChatCompletion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                )

                if self.aborted:
                    return None
                
                if not isinstance(result, ChatCompletion):
                    raise TranslationResponseError(f"Unexpected response type: {type(result).__name__}", response=result)

                if not getattr(result, 'choices'):
                    raise TranslationResponseError("No choices returned in the response", response=result)

                response['response_time'] = getattr(result, 'response_ms', 0)

                if result.usage:
                    response['prompt_tokens'] = getattr(result.usage, 'prompt_tokens')
                    response['output_tokens'] = getattr(result.usage, 'completion_tokens')
                    response['total_tokens'] = getattr(result.usage, 'total_tokens')

                if result.choices:
                    choice = result.choices[0]
                    reply = result.choices[0].message

                    response['finish_reason'] = getattr(choice, 'finish_reason', None)
                    response['text'] = getattr(reply, 'content', None)
                else:
                    raise TranslationResponseError("No choices returned in the response", response=result)

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
                    raise TranslationImpossibleError("OpenAI account quota reached, please upgrade your plan")

            except openai.APITimeoutError as e:
                if retry < self.max_retries and not self.aborted:
                    sleep_time = self.backoff_time * 2.0**retry
                    logging.warning(f"OpenAI error {str(e)}, retrying in {sleep_time}...")
                    time.sleep(sleep_time)
                    continue

            except openai.APIConnectionError as e:
                if not self.aborted:
                    raise TranslationError(str(e), error=e)

            except Exception as e:
                raise TranslationImpossibleError(f"Unexpected error communicating with OpenAI", error=e)

        raise TranslationImpossibleError(f"Failed to communicate with provider after {self.max_retries} retries")

