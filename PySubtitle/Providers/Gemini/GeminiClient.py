import logging
import time
from typing import Any

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
from PySubtitle.Helpers.Localization import _
from PySubtitle.Helpers.Settings import GetStrSetting, GetFloatSetting
from PySubtitle.Options import SettingsType
from PySubtitle.SubtitleError import TranslationImpossibleError, TranslationResponseError
from PySubtitle.Translation import Translation
from PySubtitle.TranslationClient import TranslationClient

from PySubtitle.TranslationPrompt import TranslationPrompt

class GeminiClient(TranslationClient):
    """
    Handles communication with Google Gemini to request translations
    """
    def __init__(self, settings : SettingsType):
        super().__init__(settings)

        logging.info(_("Translating with Gemini {model} model").format(
            model=self.model or _("default")
        ))

        self.safety_settings: list[SafetySetting] = [
            SafetySetting(category=HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(category=HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(category=HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY, threshold=HarmBlockThreshold.BLOCK_NONE)
        ]

        self.automatic_function_calling: AutomaticFunctionCallingConfig = AutomaticFunctionCallingConfig(disable=True, maximum_remote_calls=None)

    @property
    def api_key(self) -> str|None:
        return GetStrSetting(self.settings, 'api_key')

    @property
    def model(self) -> str|None:
        return GetStrSetting(self.settings, 'model')

    @property
    def rate_limit(self) -> float|None:
        return GetFloatSetting(self.settings, 'rate_limit')

    def _request_translation(self, prompt : TranslationPrompt, temperature : float|None = None) -> Translation|None:
        """
        Request a translation based on the provided prompt
        """
        logging.debug(f"Messages:\n{FormatMessages(prompt.messages)}")

        if not isinstance(prompt.system_prompt, str):
            raise TranslationImpossibleError(_("System prompt is required"))

        if not isinstance(prompt.content, str) or not prompt.content.strip():
            raise TranslationImpossibleError(_("No content provided for translation"))
            
        temperature = temperature or self.temperature
        response = self._send_messages(prompt.system_prompt, prompt.content, temperature)

        return Translation(response) if response else None

    def _abort(self) -> None:
        # TODO cancel any ongoing requests
        return super()._abort()

    def _send_messages(self, system_instruction : str, completion : str, temperature: float) -> dict[str, Any]|None:
        """
        Make a request to the Gemini API to provide a translation
        """
        response = {}

        if not self.model:
            raise TranslationImpossibleError(_("No model specified"))

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
                    raise TranslationImpossibleError(_("No response from Gemini"))

                if gcr.prompt_feedback and gcr.prompt_feedback.block_reason:
                    raise TranslationResponseError(_("Request was blocked by Gemini: {block_reason}").format(
                        block_reason=str(gcr.prompt_feedback.block_reason)
                    ), response=gcr)

                # Try to find a validate candidate
                candidates = [candidate for candidate in gcr.candidates if candidate.content] if gcr.candidates else []
                candidates = [candidate for candidate in candidates if candidate.finish_reason == FinishReason.STOP] or candidates

                if not candidates:
                    raise TranslationResponseError(_("No valid candidates returned in the response"), response=gcr)

                candidate = candidates[0]
                response['token_count'] = candidate.token_count

                finish_reason = candidate.finish_reason
                if finish_reason == "STOP" or finish_reason == FinishReason.STOP:
                    response['finish_reason'] = "complete"
                elif finish_reason == "MAX_TOKENS" or finish_reason == FinishReason.MAX_TOKENS:
                    response['finish_reason'] = "length"
                    raise TranslationResponseError(_("Gemini response exceeded token limit"), response=candidate)
                elif finish_reason == "SAFETY" or finish_reason == FinishReason.SAFETY:
                    response['finish_reason'] = "blocked"
                    raise TranslationResponseError(_("Gemini response was blocked for safety reasons"), response=candidate)
                elif finish_reason == "RECITATION" or finish_reason == FinishReason.RECITATION:
                    response['finish_reason'] = "recitation"
                    raise TranslationResponseError(_("Gemini response was blocked for recitation"), response=candidate)
                elif finish_reason == "FINISH_REASON_UNSPECIFIED" or finish_reason == FinishReason.FINISH_REASON_UNSPECIFIED:
                    response['finish_reason'] = "unspecified"
                    raise TranslationResponseError(_("Gemini response was incomplete"), response=candidate)
                else:
                    # Probably a failure
                    response['finish_reason'] = finish_reason

                usage_metadata : GenerateContentResponseUsageMetadata|None = gcr.usage_metadata
                if usage_metadata:
                    response['prompt_tokens'] = usage_metadata.prompt_token_count
                    response['output_tokens'] = usage_metadata.candidates_token_count
                    response['total_tokens'] = usage_metadata.total_token_count

                if not candidate or not candidate.content or not candidate.content.parts:
                    raise TranslationResponseError(_("Gemini response has no valid content parts"), response=candidate)

                response_text = "\n".join(part.text for part in candidate.content.parts if part.text)

                if not response_text:
                    raise TranslationResponseError(_("Gemini response is empty"), response=candidate)

                response['text'] = response_text

                thoughts = "\n".join(part.text for part in candidate.content.parts if part.thought and part.text)
                if thoughts:
                    response['reasoning'] = thoughts

                return response

            except Exception as e:
                if retry == self.max_retries:
                    raise TranslationImpossibleError(_("Failed to communicate with provider after {max_retries} retries").format(
                        max_retries=self.max_retries
                    ))

                if not self.aborted:
                    sleep_time = self.backoff_time * 2.0**retry
                    logging.warning(_("Gemini request failure {error}, retrying in {sleep_time} seconds...").format(
                        error=str(e), sleep_time=sleep_time
                    ))
                    time.sleep(sleep_time)

