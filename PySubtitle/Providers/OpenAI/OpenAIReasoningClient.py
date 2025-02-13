from openai.types.chat import ChatCompletion

from PySubtitle.Providers.OpenAI.OpenAIClient import OpenAIClient
from PySubtitle.SubtitleError import TranslationResponseError

linesep = '\n'

class OpenAIReasoningClient(OpenAIClient):
    """
    Handles chat communication with OpenAI to request translations
    """
    def __init__(self, settings : dict):
        settings['supports_system_messages'] = True
        settings['supports_conversation'] = True
        settings['supports_reasoning'] = True
        super().__init__(settings)

    @property
    def reasoning_effort(self):
        return self.settings.get('reasoning_effort', "low")

    def _send_messages(self, messages : list[str], temperature):
        """
        Make a request to an OpenAI-compatible API to provide a translation
        """
        response = {}

        result : ChatCompletion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            reasoning_effort=self.reasoning_effort
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
            completion_tokens_details = getattr(result.usage, 'completion_tokens_details')
            if completion_tokens_details:
                response["reasoning_tokens"] = getattr(completion_tokens_details, 'reasoning_tokens')
                response["accepted_prediction_tokens"] = getattr(completion_tokens_details, 'accepted_prediction_tokens')
                response["rejected_prediction_tokens"] = getattr(completion_tokens_details, 'rejected_prediction_tokens')

        if result.choices:
            choice = result.choices[0]
            reply = result.choices[0].message

            response['finish_reason'] = getattr(choice, 'finish_reason', None)
            response['text'] = getattr(reply, 'content', None)
        else:
            raise TranslationResponseError("No choices returned in the response", response=result)

        # Return the response if the API call succeeds
        return response
