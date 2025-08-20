import logging
import time
from typing import Any

try:
    import anthropic

    from PySubtitle.Helpers import FormatMessages
    from PySubtitle.Helpers.Localization import _
    from PySubtitle.SubtitleError import TranslationError, TranslationResponseError, TranslationImpossibleError
    from PySubtitle.TranslationClient import TranslationClient
    from PySubtitle.Translation import Translation
    from PySubtitle.TranslationPrompt import TranslationPrompt

    linesep = '\n'

    class AnthropicClient(TranslationClient):
        """
        Handles communication with Claude via the anthropic SDK
        """
        def __init__(self, settings : dict[str, Any]):
            super().__init__(settings)

            logging.info(_("Translating with Anthropic {model}").format(
                model=self.model or _("default model")
            ))

        @property
        def api_key(self) -> str|None:
            return self.settings.get('api_key')

        @property
        def model(self) -> str|None:
            return self.settings.get('model')

        @property
        def max_tokens(self) -> int:
            return self.settings.get('max_tokens', 0)
        
        @property
        def allow_thinking(self) -> bool:
            return self.settings.get('thinking', False)
        
        @property
        def thinking(self) -> dict[str, Any] | Any:
            if self.allow_thinking:
                return {
                    'type' : 'enabled',
                    'budget_tokens' : self.settings.get('max_thinking_tokens', 1024)
                }
            
            return anthropic.NOT_GIVEN

        def _request_translation(self, prompt : TranslationPrompt, temperature : float|None = None) -> Translation|None:
            """
            Request a translation based on the provided prompt
            """
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)

                # Try to add proxy settings if specified
                if self.settings.get('proxy'):
                    http_client = anthropic.DefaultHttpxClient(
                        proxy = self.settings.get('proxy')
                    )
                    self.client = self.client.with_options(http_client=http_client)

            except Exception as e:
                raise TranslationImpossibleError(_("Failed to initialize Anthropic client"), error=e)

            logging.debug(f"Messages:\n{FormatMessages(prompt.messages)}")

            temperature = temperature or self.temperature

            if prompt.system_prompt is None:
                raise TranslationError(_("System prompt is required"))

            if not prompt.content:
                raise TranslationError(_("No content provided for translation"))

            response = self._send_messages(prompt.system_prompt, prompt.content, temperature)

            translation = Translation(response) if response else None

            if translation:
                if translation.quota_reached:
                    raise TranslationImpossibleError(_("Anthropic account quota reached, please upgrade your plan or wait until it renews"))

                if translation.reached_token_limit:
                    raise TranslationError(_("Too many tokens in translation"), translation=translation)

            return translation

        def _send_messages(self, system_prompt : str, messages : list[dict[str, Any]], temperature: float) -> dict[str, Any]|None:
            """
            Make a request to the LLM to provide a translation
            """
            result = {}

            for retry in range(self.max_retries + 1):
                if self.aborted:
                    return None

                try:
                    api_response = self.client.messages.create(
                        model=self.model,
                        thinking=self.thinking,
                        messages=messages,
                        system=system_prompt,
                        temperature=temperature if not self.allow_thinking else 1,
                        max_tokens=self.max_tokens
                    )

                    if self.aborted:
                        return None

                    if not api_response.content:
                        raise TranslationResponseError(_("No choices returned in the response"), response=api_response)

                    # response['response_time'] = getattr(response, 'response_ms', 0)

                    if api_response.stop_reason == 'max_tokens':
                        result['finish_reason'] = "length"
                    else:
                        result['finish_reason'] = api_response.stop_reason

                    if api_response.usage:
                        result['prompt_tokens'] = getattr(api_response.usage, 'input_tokens')
                        result['output_tokens'] = getattr(api_response.usage, 'output_tokens')

                    for piece in api_response.content:
                        if piece.type == 'thinking':
                            result['reasoning'] = piece.thinking
                        elif piece.type == 'redacted_thinking':
                            result['reasoning'] = "Reasoning redacted by API"
                        elif piece.type == 'text':
                            result['text'] = piece.text
                            break

                    # Return the response if the API call succeeds
                    return result

                except (anthropic.APITimeoutError, anthropic.RateLimitError) as e:
                    if retry < self.max_retries and not self.aborted:
                        sleep_time = self.backoff_time * 2.0**retry
                        logging.warning(_("Anthropic API error: {error}, retrying in {sleep_time} seconds...").format(
                            error=self._get_error_message(e), sleep_time=sleep_time
                        ))
                        time.sleep(sleep_time)
                        continue

                except anthropic.APIError as e:
                    raise TranslationImpossibleError(self._get_error_message(e), error=e)

                except Exception as e:
                    raise TranslationError(_("Error communicating with provider"), error=e)

            raise TranslationImpossibleError(_("Failed to communicate with provider after {max_retries} retries").format(
                max_retries=self.max_retries
            ))

        def _get_error_message(self, e : anthropic.APIError) -> str:
            return e.message or (e.body.get('error', {}).get('message', e.message) if hasattr(e, 'body') else str(e))

except ImportError as e:
    logging.debug(f"Failed to import anthropic: {e}")
