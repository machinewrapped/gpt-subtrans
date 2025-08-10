import importlib.util
import logging
import os

if not importlib.util.find_spec("openai"):
    logging.info("OpenAI SDK is not installed. OpenAI provider will not be available")
else:
    try:
        import openai

        from PySubtitle.Helpers import GetEnvFloat
        from PySubtitle.Providers.OpenAI.ChatGPTClient import ChatGPTClient
        from PySubtitle.Providers.OpenAI.InstructGPTClient import InstructGPTClient
        from PySubtitle.Providers.OpenAI.OpenAIReasoningClient import OpenAIReasoningClient
        from PySubtitle.SubtitleError import ProviderError
        from PySubtitle.TranslationClient import TranslationClient
        from PySubtitle.TranslationProvider import TranslationProvider

        class OpenAiProvider(TranslationProvider):
            name = "OpenAI"

            information = """
            <p>Select the AI <a href="https://platform.openai.com/docs/models">model</a> to use as a translator.</p>
            <p>Note that different models have different <a href="https://openai.com/pricing">costs</a> and limitations.</p>
            In particular, the number of tokens supported by each model will affect the batch size that it can handle.
            This will depend on the contents but as a rule of thumb 16K token models can handle 80-100 lines per batch.</p>
            <p>GPT4 models are substantially more expensive but are better at following instructions,
            e.g. using provided names, and may be better for more complex translations and less common languages.</p>
            """

            information_instructmodels = "<p>Instruct models require the maximum output tokens to be specified. This should be roughly half the maximum tokens the model supports.</p>"

            information_noapikey = """
            <p>To use this provider you need <a href="https://platform.openai.com/account/api-keys">an OpenAI API key</a>.</p>
            <p>Api Base can usually be left blank unless you are using a custom OpenAI instance, when you will need to provide the base URL.</p>
            <p>Note that if your API Key is attached to a free trial account the <a href="https://platform.openai.com/docs/guides/rate-limits?context=tier-free">rate limit</a> for requests will be <i>severely</i> limited.</p>
            """

            def __init__(self, settings : dict):
                super().__init__(self.name, {
                    "api_key": settings.get('api_key', os.getenv('OPENAI_API_KEY')),
                    "api_base": settings.get('api_base', os.getenv('OPENAI_API_BASE')),
                    "model": settings.get('model', os.getenv('OPENAI_MODEL', "gpt-5-mini")),
                    'temperature': settings.get('temperature', GetEnvFloat('OPENAI_TEMPERATURE', 0.0)),
                    'rate_limit': settings.get('rate_limit', GetEnvFloat('OPENAI_RATE_LIMIT')),
                    "free_plan": settings.get('free_plan', os.getenv('OPENAI_FREE_PLAN') == "True"),
                    'max_instruct_tokens': settings.get('max_instruct_tokens', int(os.getenv('MAX_INSTRUCT_TOKENS', 2048))),
                    'use_httpx': settings.get('use_httpx', os.getenv('OPENAI_USE_HTTPX', "False") == "True"),
                    'reasoning_effort': settings.get('reasoning_effort', os.getenv('OPENAI_REASONING_EFFORT', "low")),
                })

                self.refresh_when_changed = ['api_key', 'api_base', 'model']

                self.valid_model_types = [ "gpt", "o1", "o3", "o4" ]
                self.excluded_model_types = [ "vision", "realtime", "audio" ]
                self.reasoning_models = [ "o1","o3","o4","gpt-5" ]

            @property
            def api_key(self):
                return self.settings.get('api_key')

            @property
            def api_base(self):
                return self.settings.get('api_base')

            @property
            def is_instruct_model(self):
                return self.selected_model and self.selected_model.find("instruct") >= 0

            @property
            def is_reasoning_model(self):
                return self.selected_model and any(self.selected_model.startswith(reasoning_model) for reasoning_model in self.reasoning_models)

            def GetTranslationClient(self, settings : dict) -> TranslationClient:
                client_settings = self.settings.copy()
                client_settings.update(settings)
                if self.is_instruct_model:
                    return InstructGPTClient(client_settings)
                elif self.is_reasoning_model:
                    return OpenAIReasoningClient(client_settings)
                else:
                    return ChatGPTClient(client_settings)

            def GetOptions(self) -> dict:
                options = {
                    'api_key': (str, "An OpenAI API key is required to use this provider (https://platform.openai.com/account/api-keys)"),
                    'api_base': (str, "The base URL to use for requests - leave as default unless you know you need something else"),
                }

                if self.api_base:
                    options['use_httpx'] = (bool, "Use the httpx library for requests. May help if you receive a 307 redirect error with a custom api_base")

                if self.api_key:
                    models = self.available_models
                    if models:
                        options.update({
                            'model': (models, "AI model to use as the translator" if models else "Unable to retrieve models"),
                            'rate_limit': (float, "Maximum OpenAI API requests per minute. Mainly useful if you are on the restricted free plan")
                        })

                        if self.is_instruct_model:
                            options['max_instruct_tokens'] = (int, "Maximum tokens a completion can contain (only applicable for -instruct models)")

                        if self.is_reasoning_model:
                            options['reasoning_effort'] = (["low", "medium", "high"], "The level of reasoning effort to use for the model")
                        else:
                            options['temperature'] = (float, "Amount of random variance to add to translations. Generally speaking, none is best")

                    else:
                        options['model'] = (["Unable to retrieve models"], "Check API key and base URL and try again")

                return options

            def GetAvailableModels(self) -> list[str]:
                """
                Returns a list of possible values for the LLM model
                """
                try:
                    if not hasattr(openai, "OpenAI"):
                        raise ProviderError("The OpenAI library is out of date and must be updated", provider=self)

                    if not self.api_key:
                        logging.debug("No OpenAI API key provided")
                        return []

                    client = openai.OpenAI(
                        api_key=self.api_key,
                        base_url=self.api_base or None
                    )
                    response = client.models.list()

                    if not response or not response.data:
                        return []

                    model_list = [ model.id for model in response.data if any(model.id.startswith(prefix) for prefix in self.valid_model_types) ]

                    model_list = [ model for model in model_list if not any([ model.find(exclude) >= 0 for exclude in self.excluded_model_types ]) ]

                    # Maybe this isn't really an OpenAI endpoint, just return all the available models
                    if not model_list:
                        model_list = [ model.id for model in response.data ]

                    return sorted(model_list)

                except Exception as e:
                    logging.error(f"Unable to retrieve available AI models: {str(e)}")
                    return []

            def GetInformation(self) -> str:
                if not self.api_key:
                    return self.information_noapikey
                if self.is_instruct_model:
                    return self.information + self.information_instructmodels
                return self.information

            def ValidateSettings(self) -> bool:
                """
                Validate the settings for the provider
                """
                if not self.api_key:
                    self.validation_message = "API Key is required"
                    return False

                return True

            def _allow_multithreaded_translation(self) -> bool:
                """
                If user is on the free plan or has set a rate limit it is better not to try parallel requests
                """
                if self.settings.get('free_plan'):
                    return False

                if self.settings.get('rate_limit', 0.0) != 0.0:
                    return False

                return True

    except ImportError:
        logging.info("Failed to initialise OpenAI SDK. OpenAI provider will not be available")