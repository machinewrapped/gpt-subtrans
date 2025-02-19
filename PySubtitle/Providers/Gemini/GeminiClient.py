import logging
import time

from google import genai
from google.genai.types import (
    AutomaticFunctionCallingConfig,
    FinishReason,
    GenerateContentConfig,
    GenerateContentResponse,
    GenerateContentResponseUsageMetadata,
    HarmBlockMethod,
    HarmBlockThreshold,
    HarmCategory,
    Part,
    SafetySetting
)

from PySubtitle.Helpers import FormatMessages
from PySubtitle.SubtitleError import TranslationImpossibleError, TranslationResponseError
from PySubtitle.Translation import Translation
from PySubtitle.TranslationClient import TranslationClient

from PySubtitle.TranslationPrompt import TranslationPrompt

class GeminiClient(TranslationClient):
    """
    Handles communication with Google Gemini to request translations
    """
    def __init__(self, settings : dict):
        super().__init__(settings)

        logging.info(f"Translating with Gemini {self.model or 'default'} model")

        self.safety_settings = [
            SafetySetting(category=HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(category=HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(category=HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY, threshold=HarmBlockThreshold.BLOCK_NONE)
        ]

        self.automatic_function_calling = AutomaticFunctionCallingConfig(disable=True, maximum_remote_calls=None)

    @property
    def api_key(self):
        return self.settings.get('api_key')

    @property
    def model(self):
        return self.settings.get('model')

    @property
    def rate_limit(self):
        return self.settings.get('rate_limit')

    def _request_translation(self, prompt : TranslationPrompt, temperature : float = None) -> Translation:
        """
        Request a translation based on the provided prompt
        """
        logging.debug(f"Messages:\n{FormatMessages(prompt.messages)}")

        temperature = temperature or self.temperature
        response = self._send_messages(prompt.system_prompt, prompt.content, temperature)

        return Translation(response) if response else None

    def _abort(self):
        # TODO cancel any ongoing requests
        return super()._abort()

    def _send_messages(self, system_instruction : str, completion : str, temperature):
        """
        Make a request to the Gemini API to provide a translation
        """
        response = {}

        for retry in range(1 + self.max_retries):
            try:
                gemini_client = genai.Client(api_key=self.api_key, http_options={'api_version': 'v1alpha'})
                config = GenerateContentConfig(
                    candidate_count=1,
                    temperature=temperature,
                    system_instruction=system_instruction,
                    automatic_function_calling=self.automatic_function_calling,
                    max_output_tokens=None,
                    response_modalities=[]
                )
                gcr : GenerateContentResponse = gemini_client.models.generate_content(
                    model=self.model,
                    contents=Part.from_text(text=completion),
                    config=config
                    )

                if self.aborted:
                    return None

                if not gcr:
                    raise TranslationImpossibleError("No response from Gemini")

                if gcr.prompt_feedback and gcr.prompt_feedback.block_reason:
                    raise TranslationResponseError(f"Request was blocked by Gemini: {str(gcr.prompt_feedback.block_reason)}", response=gcr)

                # Try to find a validate candidate
                candidates = [candidate for candidate in gcr.candidates if candidate.content]
                candidates = [candidate for candidate in candidates if candidate.finish_reason == FinishReason.STOP] or candidates

                if not candidates:
                    raise TranslationResponseError("No valid candidates returned in the response", response=gcr)

                candidate = candidates[0]
                response['token_count'] = candidate.token_count

                finish_reason = candidate.finish_reason
                if finish_reason == "STOP" or finish_reason == FinishReason.STOP:
                    response['finish_reason'] = "complete"
                elif finish_reason == "MAX_TOKENS" or finish_reason == FinishReason.MAX_TOKENS:
                    response['finish_reason'] = "length"
                    raise TranslationResponseError("Gemini response exceeded token limit", response=candidate)
                elif finish_reason == "SAFETY" or finish_reason == FinishReason.SAFETY:
                    response['finish_reason'] = "blocked"
                    raise TranslationResponseError("Gemini response was blocked for safety reasons", response=candidate)
                elif finish_reason == "RECITATION" or finish_reason == FinishReason.RECITATION:
                    response['finish_reason'] = "recitation"
                    raise TranslationResponseError("Gemini response was blocked for recitation", response=candidate)
                elif finish_reason == "FINISH_REASON_UNSPECIFIED" or finish_reason == FinishReason.FINISH_REASON_UNSPECIFIED:
                    response['finish_reason'] = "unspecified"
                    raise TranslationResponseError("Gemini response was incomplete", response=candidate)
                else:
                    # Probably a failure
                    response['finish_reason'] = finish_reason

                usage_metadata : GenerateContentResponseUsageMetadata = gcr.usage_metadata
                if usage_metadata:
                    response['prompt_tokens'] = usage_metadata.prompt_token_count
                    response['output_tokens'] = usage_metadata.candidates_token_count
                    response['total_tokens'] = usage_metadata.total_token_count

                if not candidate.content.parts:
                    raise TranslationResponseError("Gemini response has no valid content parts", response=candidate)

                response_text = "\n".join(part.text for part in candidate.content.parts)

                if not response_text:
                    raise TranslationResponseError("Gemini response is empty", response=candidate)

                response['text'] = response_text

                thoughts = "\n".join(part.thought for part in candidate.content.parts if part.thought)
                if thoughts:
                    response['reasoning'] = thoughts

                return response

            except Exception as e:
                if retry == self.max_retries:
                    raise TranslationImpossibleError(f"Failed to communicate with provider after {self.max_retries} retries")

                if not self.aborted:
                    sleep_time = self.backoff_time * 2.0**retry
                    logging.warning(f"Gemini request failure {str(e)}, retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)

