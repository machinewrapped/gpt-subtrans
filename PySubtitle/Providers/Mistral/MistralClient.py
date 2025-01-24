import logging

from PySubtitle.SubtitleError import TranslationResponseError

try:
    import mistralai
    from mistralai.models import ChatCompletionResponse as ChatCompletion

    from PySubtitle.Helpers import FormatMessages
    from PySubtitle.SubtitleError import TranslationError, TranslationImpossibleError
    from PySubtitle.Translation import Translation
    from PySubtitle.TranslationClient import TranslationClient
    from PySubtitle.TranslationPrompt import TranslationPrompt

    class MistralClient(TranslationClient):
        """
        Handles communication with Mistral to request translations
        """
        def __init__(self, settings : dict):
            super().__init__(settings)

            if not self.api_key:
                raise TranslationImpossibleError('API key must be set in .env or provided as an argument')

            logging.info(f"Translating with Mistral model {self.model or 'default'}, using server: {self.server_url or 'default'}")

            self.client = mistralai.Mistral(api_key=self.api_key, server_url=self.server_url)

        @property
        def api_key(self):
            return self.settings.get('api_key')

        @property
        def server_url(self):
            return self.settings.get('server_url')

        @property
        def model(self):
            return self.settings.get('model')

        def _request_translation(self, prompt : TranslationPrompt, temperature : float = None) -> Translation:
            """
            Request a translation based on the provided prompt
            """
            logging.debug(f"Messages:\n{FormatMessages(prompt.messages)}")

            temperature = temperature or self.temperature
            response = self._send_messages(prompt.content, temperature)

            translation = Translation(response) if response else None

            if translation:
                if translation.quota_reached:
                    raise TranslationImpossibleError("Mistral account quota reached, please upgrade your plan or wait until it renews")

                if translation.reached_token_limit:
                    raise TranslationError(f"Too many tokens in translation", translation=translation)

            return translation

        def _send_messages(self, messages : list[str], temperature):
            """
            Make a request to an Mistralai-compatible API to provide a translation
            """
            response = {}

            for retry in range(self.max_retries + 1):
                if self.aborted:
                    return None

                try:
                    result : ChatCompletion = self.client.chat.complete(
                        model=self.model,
                        messages=messages,
                        temperature=temperature,
                        server_url=self.server_url if self.server_url else None
                    )

                    if self.aborted:
                        return None

                    if not isinstance(result, ChatCompletion):
                        raise TranslationResponseError(f"Unexpected response type: {type(result).__name__}", response=result)

                    if not getattr(result, 'choices'):
                        raise TranslationResponseError("No choices returned in the response", response=result)

                    response['response_time'] = getattr(result, 'response_ms', 0)

                    if hasattr(result, "usage"):
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

                except Exception as e:
                    #TODO: find out what specific exceptions mistralai raises
                    raise TranslationImpossibleError(f"Unexpected error communicating with the provider", error=e)

            raise TranslationImpossibleError(f"Failed to communicate with provider after {self.max_retries} retries")

except ImportError as e:
    logging.debug(f"Failed to import mistralai: {e}")
