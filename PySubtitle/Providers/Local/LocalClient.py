import logging
import time
import httpx

from PySubtitle.Helpers import FormatMessages
from PySubtitle.SubtitleError import TranslationError, TranslationImpossibleError, TranslationResponseError
from PySubtitle.Translation import Translation
from PySubtitle.TranslationClient import TranslationClient
from PySubtitle.TranslationParser import TranslationParser
from PySubtitle.TranslationPrompt import TranslationPrompt

class LocalClient(TranslationClient):
    """
    Handles communication with local LLM server to request translations
    """
    def __init__(self, settings : dict):
        super().__init__(settings)
        self.client = None

        logging.info(f"Translating with local server at {self.server_address}{self.endpoint}")

    @property
    def server_address(self):
        return self.settings.get('server_address')
    
    @property
    def endpoint(self):
        return self.settings.get('endpoint')
    
    @property
    def supports_conversation(self):
        return self.settings.get('supports_conversation', False)
    
    @property
    def max_tokens(self):
        return self.settings.get('max_tokens', -1)
    
    def _request_translation(self, prompt : TranslationPrompt, temperature : float = None) -> Translation:
        """
        Request a translation based on the provided prompt
        """
        logging.debug(f"Messages:\n{FormatMessages(prompt.messages)}")

        temperature = temperature or self.temperature
        response = self._make_request(prompt, temperature)

        translation = Translation(response) if response else None

        return translation

    def GetParser(self):
        return TranslationParser(self.settings)

    def _abort(self):
        if self.client:
            self.client.close()
        return super()._abort()

    def _make_request(self, prompt : TranslationPrompt, temperature):
        """
        Make a request to the server to provide a translation
        """
        response = {}

        for retry in range(self.max_retries + 1):
            if self.aborted:
                return None

            try:
                max_tokens = self.max_tokens if self.max_tokens else -1
                request_body = self._generate_request_body(prompt, temperature, max_tokens)
                logging.debug(f"Request Body:\n{request_body}")

                self.client = httpx.Client(base_url=self.server_address, follow_redirects=True, timeout=300.0, headers={'Content-Type': 'application/json'})

                result : httpx.Response = self.client.post(self.endpoint, json=request_body)

                if self.aborted:
                    return None
                
                logging.debug(f"Response:\n{result.text}")

                content = result.json()

                response['model'] = content.get('model')
                response['response_time'] = content.get('response_ms', 0)

                usage = content.get('usage', {})
                response['prompt_tokens'] = usage.get('prompt_tokens')
                response['output_tokens'] = usage.get('completion_tokens')
                response['total_tokens'] = usage.get('total_tokens')

                choices = content.get('choices')
                if not choices:
                    raise TranslationResponseError("No choices returned in the response", response=result)

                for choice in choices:
                    if choice.get('text'):
                        response['text'] = choice.get('text')
                        response['finish_reason'] = choice.get('finish_reason')
                        break

                    if choice.get('message'):
                        response['text'] = choice.get('message', {}).get('content')
                        response['finish_reason'] = choice.get('finish_reason')
                        break
                
                if not response.get('text'):
                    raise TranslationResponseError("No text returned in the response", response=result)

                # Return the response if the API call succeeds
                return response
            
            except httpx.ConnectError as e:
                if self.aborted:
                    return None

                logging.error(f"Failed to connect to server at {self.server_address}{self.endpoint}")
                continue

            except httpx.NetworkError as e:
                if self.aborted:
                    return None

                raise TranslationError(str(e), error=e)
        
            except httpx.ReadTimeout as e:
                raise TranslationError("Request to server timed out", error=e)

            except Exception as e:
                raise TranslationImpossibleError(f"Unexpected error communicating with server", error=e)

        raise TranslationImpossibleError(f"Failed to communicate with server after {self.max_retries} retries")

    def _generate_request_body(self, prompt, temperature, max_tokens):
        request_body = {
            'temperature': temperature,
            'max_tokens': max_tokens,
            'stream': False
        }

        if self.supports_conversation:
            request_body['messages'] = prompt.messages
        else:
            request_body['prompt'] = prompt.content

        return request_body

