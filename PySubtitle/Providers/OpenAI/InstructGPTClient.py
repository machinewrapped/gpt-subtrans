from openai.types.completion import Completion

from PySubtitle.Providers.OpenAI.OpenAIClient import OpenAIClient
from PySubtitle.SubtitleError import TranslationResponseError

linesep = '\n'

class InstructGPTClient(OpenAIClient):
    """
    Handles communication with GPT instruct models to request translations
    """
    def __init__(self, settings : dict):
        settings['supports_conversation'] = False
        settings['supports_system_messages'] = False
        super().__init__(settings)

    @property
    def max_instruct_tokens(self):
        return self.settings.get('max_instruct_tokens', 2048)

    def _send_messages(self, prompt : str, temperature):
        """
        Make a request to the OpenAI API to provide a translation
        """
        response = {}

        result : Completion = self.client.completions.create(
            model=self.model,
            prompt=prompt,
            temperature=temperature,
            n=1,
            max_tokens=self.max_instruct_tokens
        )

        if self.aborted:
            return None

        if not isinstance(result, Completion):
            raise TranslationResponseError(f"Unexpected response type: {type(result).__name__}", response=result)

        response['response_time'] = getattr(result, 'response_ms', 0)

        if result.usage:
            response['prompt_tokens'] = getattr(result.usage, 'prompt_tokens')
            response['output_tokens'] = getattr(result.usage, 'completion_tokens')
            response['total_tokens'] = getattr(result.usage, 'total_tokens')

        if result.choices:
            choice = result.choices[0]
            if not isinstance(choice.text, str):
                raise TranslationResponseError("Instruct model completion text is not a string", response=result)

            response['finish_reason'] = getattr(choice, 'finish_reason', None)
            response['text'] = choice.text
        else:
            raise TranslationResponseError("No choices returned in the response", response=result)

        # Return the response content if the API call succeeds
        return response

