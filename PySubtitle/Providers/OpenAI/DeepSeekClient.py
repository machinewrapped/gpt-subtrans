from openai.types.chat import ChatCompletion

from PySubtitle.Helpers.Localization import _
from PySubtitle.Providers.OpenAI.OpenAIClient import OpenAIClient
from PySubtitle.SubtitleError import TranslationResponseError
from PySubtitle.TranslationPrompt import TranslationPrompt

linesep = '\n'

class DeepSeekClient(OpenAIClient):
    """
    Handles chat communication with DeepSeek to request translations
    """
    def __init__(self, settings : dict):
        settings['supports_system_messages'] = True
        settings['supports_conversation'] = True
        settings['supports_reasoning'] = True
        super().__init__(settings)

    @property
    def max_tokens(self):
        return self.settings.get('max_tokens', None)

    def _send_messages(self, prompt : TranslationPrompt, temperature):
        """
        Make a request to DeepSeek's OpenAI-compatible API to provide a translation
        """
        response = {}
        messages : list[dict] = prompt.content

        result : ChatCompletion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=self.max_tokens
        )

        if self.aborted:
            return None

        if not isinstance(result, ChatCompletion):
            raise TranslationResponseError(_("Unexpected response type: {response_type}").format(
                response_type=type(result).__name__
            ), response=result)

        if not getattr(result, 'choices'):
            raise TranslationResponseError(_("No choices returned in the response"), response=result)

        response['response_time'] = getattr(result, 'response_ms', 0)

        if result.usage:
            response['prompt_tokens'] = getattr(result.usage, 'prompt_tokens')
            response['output_tokens'] = getattr(result.usage, 'completion_tokens')
            response['total_tokens'] = getattr(result.usage, 'total_tokens')
            completion_tokens_details = getattr(result.usage, 'completion_tokens_details')
            if completion_tokens_details:
                response["reasoning_tokens"] = getattr(completion_tokens_details, 'reasoning_tokens')

        if result.choices:
            choice = result.choices[0]
            reply = result.choices[0].message

            model_extra = getattr(reply, 'model_extra', None)
            if model_extra:
                reasoning_content = model_extra.get('reasoning_content', None)
                if reasoning_content:
                    response['reasoning'] = reasoning_content

            response['finish_reason'] = getattr(choice, 'finish_reason', None)
            response['text'] = getattr(reply, 'content', None)

        else:
            raise TranslationResponseError(_("No choices returned in the response"), response=result)

        # Return the response if the API call succeeds
        return response

