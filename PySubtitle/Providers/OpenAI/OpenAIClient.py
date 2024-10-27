import logging
from typing import Optional
from pydantic import BaseModel, Field

try:
    import openai
    import httpx

    from PySubtitle.Helpers import FormatMessages
    from PySubtitle.SubtitleError import TranslationError, TranslationImpossibleError
    from PySubtitle.Translation import Translation
    from PySubtitle.TranslationClient import TranslationClient
    from PySubtitle.TranslationParser import TranslationParser
    from PySubtitle.TranslationPrompt import TranslationPrompt

    class OpenAISettings(BaseModel):
        """
        Configuration settings for OpenAI client using Pydantic for validation
        """
        api_key: Optional[str] = Field(None, description="OpenAI API key")
        api_base: Optional[str] = Field(None, description="Custom API base URL")
        model: Optional[str] = Field(None, description="OpenAI model to use")
        temperature: float = Field(0.0, description="Sampling temperature")
        proxy: Optional[str] = Field(None, description="Proxy URL")
        use_httpx: bool = Field(False, description="Use httpx client")
        max_retries: int = Field(3, description="Maximum number of retry attempts")
        backoff_time: float = Field(1.0, description="Initial backoff time for retries")
        max_instruct_tokens: int = Field(2048, description="Maximum tokens for instruct models")
        supports_system_messages: bool = Field(False, description="Whether the model supports system messages")
        supports_conversation: bool = Field(False, description="Whether the model supports conversation")

    class OpenAIClient(TranslationClient):
        """
        Handles communication with OpenAI to request translations
        """
        def __init__(self, settings: dict):
            super().__init__(settings)
            
            # Convert dictionary settings to Pydantic model
            self.config = OpenAISettings(
                api_key=settings.get('api_key'),
                api_base=settings.get('api_base'),
                model=settings.get('model'),
                temperature=settings.get('temperature', 0.0),
                proxy=settings.get('proxy'),
                use_httpx=settings.get('use_httpx', False),
                max_retries=settings.get('max_retries', 3),
                backoff_time=settings.get('backoff_time', 1.0),
                max_instruct_tokens=settings.get('max_instruct_tokens', 2048),
                supports_system_messages=settings.get('supports_system_messages', False),
                supports_conversation=settings.get('supports_conversation', False)
            )

            if not hasattr(openai, "OpenAI"):
                raise TranslationImpossibleError("The OpenAI library is out of date and must be updated")

            # Set API key with fallback to environment variable
            openai.api_key = self.config.api_key or openai.api_key

            if not openai.api_key:
                raise TranslationImpossibleError('API key must be set in .env or provided as an argument')

            # Configure base URL if provided
            if self.config.api_base:
                openai.base_url = self.config.api_base

            logging.info(f"Translating with OpenAI model {self.config.model or 'default'}, Using API Base: {openai.base_url}")

            # Configure HTTP client
            http_client = None
            if self.config.proxy:
                proxies = {
                    'http://': self.config.proxy,
                    'https://': self.config.proxy
                }
                http_client = httpx.Client(proxies=proxies)
            elif self.config.use_httpx:
                http_client = httpx.Client(base_url=openai.base_url, follow_redirects=True)

            self.client = openai.OpenAI(
                api_key=openai.api_key,
                base_url=openai.base_url,
                http_client=http_client
            )

        @property
        def api_key(self):
            return self.config.api_key

        @property
        def api_base(self):
            return self.config.api_base

        @property
        def model(self):
            return self.config.model

        @property
        def temperature(self):
            return self.config.temperature

        @property
        def max_retries(self):
            return self.config.max_retries

        @property
        def backoff_time(self):
            return self.config.backoff_time

        @property
        def max_instruct_tokens(self):
            return self.config.max_instruct_tokens

        @property
        def supports_system_messages(self):
            return self.config.supports_system_messages

        @property
        def supports_conversation(self):
            return self.config.supports_conversation

        def _request_translation(self, prompt: TranslationPrompt, temperature: float = None) -> Translation:
            """
            Request a translation based on the provided prompt
            """
            logging.debug(f"Messages:\n{FormatMessages(prompt.messages)}")

            temperature = temperature or self.temperature
            response = self._send_messages(prompt.content, temperature)

            translation = Translation(response) if response else None

            if translation:
                if translation.quota_reached:
                    raise TranslationImpossibleError("OpenAI account quota reached, please upgrade your plan or wait until it renews")

                if translation.reached_token_limit:
                    raise TranslationError(f"Too many tokens in translation", translation=translation)

            return translation

        def _send_messages(self, content, temperature: float):
            """
            Communicate with the API
            """
            raise NotImplementedError

        def _abort(self):
            self.client.close()
            return super()._abort()

except ImportError as e:
    logging.debug(f"Failed to import openai: {e}")
