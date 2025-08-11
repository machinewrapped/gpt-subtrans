from json import JSONDecodeError
import logging
import time

from PySubtitle.Helpers.Parse import ParseDelayFromHeader
from PySubtitle.SubtitleError import TranslationResponseError

try:
    import openai
    import httpx

    from PySubtitle.Helpers import FormatMessages
    from PySubtitle.SubtitleError import TranslationError, TranslationImpossibleError
    from PySubtitle.Translation import Translation
    from PySubtitle.TranslationClient import TranslationClient
    from PySubtitle.TranslationPrompt import TranslationPrompt

    class OpenAIClient(TranslationClient):
        """
        Handles communication with OpenAI to request translations
        """
        def __init__(self, settings : dict):
            super().__init__(settings)

            if not hasattr(openai, "OpenAI"):
                raise TranslationImpossibleError("The OpenAI library is out of date and must be updated")

            openai.api_key = self.api_key or openai.api_key

            if not openai.api_key:
                raise TranslationImpossibleError('API key must be set in .env or provided as an argument')

            logging.info(f"Translating with model {self.model or 'default'}, Using API Base: {self.api_base or openai.base_url}")

            self.client = None

        @property
        def api_key(self):
            return self.settings.get('api_key')

        @property
        def api_base(self):
            return self.settings.get('api_base')

        @property
        def model(self):
            return self.settings.get('model')
        
        @property
        def reuse_client(self):
            return self.settings.get('reuse_client', True)

        def _request_translation(self, prompt : TranslationPrompt, temperature : float = None) -> Translation:
            """
            Request a translation based on the provided prompt
            """
            logging.debug(f"Messages:\n{FormatMessages(prompt.messages)}")

            # If we're using a new client for each request, create it here
            temperature = temperature or self.temperature

            response = self._try_send_messages(prompt, temperature)

            translation = Translation(response) if response else None

            if translation:
                if translation.quota_reached:
                    raise TranslationImpossibleError("Account quota reached, please upgrade your plan or wait until it renews")

                if translation.reached_token_limit:
                    raise TranslationError(f"Too many tokens in translation", translation=translation)

            return translation

        def _send_messages(self, messages : list[str], temperature : float):
            """
            Communicate with the API
            """
            raise NotImplementedError

        def _abort(self):
            self.client.close()
            return super()._abort()
        
        def _try_send_messages(self, prompt : TranslationPrompt, temperature: float):
            for retry in range(self.max_retries + 1):
                if self.aborted:
                    return None

                backoff_time = self.backoff_time * 2.0**retry

                try:
                    if not self.client or not self.reuse_client:
                        self._create_client()

                    response = self._send_messages(prompt, temperature)

                    return response
                
                except TranslationResponseError as e:
                    if retry < self.max_retries and not self.aborted:
                        logging.warning(f"{str(e)}, retrying in {backoff_time} seconds...")
                        time.sleep(backoff_time)
                        continue

                except openai.RateLimitError as e:
                    if not self.aborted:
                        retry_after = e.response.headers.get('x-ratelimit-reset-requests') or e.response.headers.get('Retry-After')
                        if retry_after:
                            backoff_time = ParseDelayFromHeader(retry_after)
                            logging.warning(f"Rate limit hit, retrying in {backoff_time} seconds...")
                            time.sleep(backoff_time)
                            continue
                        else:
                            raise TranslationImpossibleError("Account quota reached, please upgrade your plan")

                except openai.APITimeoutError as e:
                    if retry < self.max_retries and not self.aborted:
                        logging.warning(f"API Timeout, retrying in {backoff_time} seconds...")
                        time.sleep(backoff_time)
                        continue

                except JSONDecodeError as e:
                    if retry < self.max_retries and not self.aborted:
                        logging.warning(f"Invalid response received, retrying in {backoff_time} seconds...")
                        time.sleep(backoff_time)
                        continue

                except openai.APIConnectionError as e:
                    if not self.aborted:
                        raise TranslationError(str(e), error=e)

                except Exception as e:
                    raise TranslationImpossibleError(f"Unexpected error communicating with the provider", error=e)

            if not self.aborted:
                raise TranslationImpossibleError(f"Failed to communicate with provider after {self.max_retries} retries")

        def _create_client(self):
            http_client = None
            if self.settings.get('proxy'):
                # Use httpx with SOCKS proxy support
                proxies = {
                    'http://': self.settings.get('proxy'),
                    'https://': self.settings.get('proxy')
                }
                http_client = httpx.Client(proxies=proxies)
            elif self.settings.get('use_httpx'):
                 http_client = httpx.Client(base_url=self.api_base, follow_redirects=True)

            self.client = openai.OpenAI(api_key=openai.api_key, base_url=self.api_base or None, http_client=http_client)

except ImportError as e:
    logging.debug(f"Failed to import openai: {e}")
