import logging

from PySubtitle.Helpers import FormatMessages
from PySubtitle.Providers.OpenAI.OpenAIClient import OpenAIClient
from PySubtitle.SubtitleError import TranslationError, TranslationImpossibleError, TranslationResponseError
from PySubtitle.Translation import Translation
from PySubtitle.TranslationPrompt import TranslationPrompt

linesep = '\n'

class OpenAIReasoningClient(OpenAIClient):
    """
    Handles chat communication with OpenAI to request translations
    """
    def __init__(self, settings : dict):
        settings['supports_system_messages'] = True
        settings['supports_conversation'] = True
        settings['supports_reasoning'] = True
        settings['supports_system_prompt'] = True
        settings['system_role'] = 'developer'
        super().__init__(settings)

    @property
    def reasoning_effort(self):
        return self.settings.get('reasoning_effort', "low")
    
    def _send_messages(self, prompt : TranslationPrompt, temperature):
        """
        Make a request to an OpenAI-compatible API to provide a translation
        """
        response = {}

        # Use the newer Responses API for reasoning-capable models (gpt-5/o4/o3, etc.)
        # Temperature is not supported for reasoning models so we omit it
        result = self.client.responses.create(
            model=self.model,
            input=prompt.content,
            instructions=prompt.system_prompt,
            reasoning={"effort": self.reasoning_effort}
        )

        if self.aborted:
            return None

        # Basic sanity: Responses API should return an object with output/output_text
        if not hasattr(result, 'output') and not hasattr(result, 'output_text'):
            raise TranslationResponseError(f"Unexpected response type: {type(result).__name__}", response=result)

        # Response timing if available
        response['response_time'] = getattr(result, 'response_ms', 0)

        # Usage mapping (Responses API typically uses input_tokens/output_tokens)
        usage = getattr(result, 'usage', None)
        if usage:
            prompt_tokens = getattr(usage, 'input_tokens', None) or getattr(usage, 'prompt_tokens', None)
            output_tokens = getattr(usage, 'output_tokens', None) or getattr(usage, 'completion_tokens', None)
            total_tokens = getattr(usage, 'total_tokens', None)

            # Fallback compute if total not provided
            if total_tokens is None and (prompt_tokens is not None and output_tokens is not None):
                total_tokens = (prompt_tokens or 0) + (output_tokens or 0)

            response['prompt_tokens'] = prompt_tokens
            response['output_tokens'] = output_tokens
            response['total_tokens'] = total_tokens

            # Reasoning/token details (field names differ across SDK versions)
            details = getattr(usage, 'output_tokens_details', None) or getattr(usage, 'completion_tokens_details', None)
            if details:
                response['reasoning_tokens'] = getattr(details, 'reasoning_tokens', None)
                response['accepted_prediction_tokens'] = getattr(details, 'accepted_prediction_tokens', None)
                response['rejected_prediction_tokens'] = getattr(details, 'rejected_prediction_tokens', None)

        # Extract text from Responses output
        text = getattr(result, 'output_text', None)
        reasoning_text = None

        if not text:
            # Attempt to build text from structured output blocks
            output_blocks = getattr(result, 'output', None) or getattr(result, 'outputs', None) or []
            collected_text: list[str] = []
            collected_reasoning: list[str] = []

            def _coerce_text(val):
                try:
                    return val if isinstance(val, str) else None
                except Exception:
                    return None

            for block in output_blocks or []:
                content_list = getattr(block, 'content', None)
                if isinstance(content_list, list):
                    for item in content_list:
                        # Typed SDK objects often have a 'text' attribute
                        t = getattr(item, 'text', None)
                        if t:
                            collected_text.append(t)

                        # Some SDKs expose dict-like items
                        if isinstance(item, dict):
                            if item.get('text'):
                                collected_text.append(item['text'])
                            # Capture any explicit reasoning blocks
                            if item.get('type') == 'reasoning':
                                r_text = item.get('text') or (item.get('reasoning') or {}).get('text')
                                if r_text:
                                    collected_reasoning.append(r_text)

                else:
                    # Fallback: if content is a str
                    t = _coerce_text(content_list)
                    if t:
                        collected_text.append(t)

                # Stop reason may live per-block in some SDKs
                if 'finish_reason' not in response:
                    finish_reason = getattr(block, 'stop_reason', None) or getattr(block, 'finish_reason', None)
                    if finish_reason:
                        response['finish_reason'] = finish_reason

            text = '\n'.join([s for s in collected_text if s]) if collected_text else None
            reasoning_text = '\n'.join([s for s in collected_reasoning if s]) if collected_reasoning else None

        # Top-level stop reason
        if 'finish_reason' not in response:
            finish = getattr(result, 'stop_reason', None) or getattr(result, 'finish_reason', None)
            # Map Responses API stop reasons to legacy finish_reason values used elsewhere
            if finish == 'max_output_tokens':
                finish = 'length'
            response['finish_reason'] = finish

        response['text'] = text
        if reasoning_text:
            response['reasoning'] = reasoning_text

        if response.get('text') is None:
            raise TranslationResponseError("No text returned in the response", response=result)

        # Return the response if the API call succeeds
        return response
