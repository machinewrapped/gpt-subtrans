import logging

def _structure_messages(messages : list[str]) -> list[dict]:
    """
    Structure the messages to be sent to the API
    """
    return [
        {
            'role' : message['role'],
            'content' : [{ 'text': message['content'] }]
        }
        for message in messages]

try:
    import boto3

    from PySubtitle.Helpers import FormatMessages
    from PySubtitle.Helpers.Localization import _
    from PySubtitle.Helpers.Settings import GetStrSetting, GetIntSetting
    from PySubtitle.Translation import Translation
    from PySubtitle.TranslationClient import TranslationClient
    from PySubtitle.TranslationPrompt import TranslationPrompt
    from PySubtitle.SubtitleError import TranslationImpossibleError, TranslationResponseError

    class BedrockClient(TranslationClient):
        """
        Handles communication with Amazon Bedrock to request translations
        """
        def __init__(self, settings : Options|SettingsType):
            super().__init__(settings)

            logging.info(_("Translating with Bedrock model {model_id}, using region: {aws_region}").format(
                model_id=self.model_id, aws_region=self.aws_region
            ))

            self.client = boto3.client(
                'bedrock-runtime',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_access_key,
                region_name=self.aws_region
            )

        @property
        def access_key(self) -> str|None:
            return GetStrSetting(self.settings, 'access_key')

        @property
        def secret_access_key(self) -> str|None:
            return GetStrSetting(self.settings, 'secret_access_key')

        @property
        def aws_region(self) -> str|None:
            return GetStrSetting(self.settings, 'aws_region')

        @property
        def model_id(self) -> str|None:
            return GetStrSetting(self.settings, 'model')

        @property
        def max_tokens(self) -> int:
            return GetIntSetting(self.settings, 'max_tokens', 4096)

        def _request_translation(self, prompt : TranslationPrompt, temperature : float|None = None) -> Translation|None:
            """
            Request a translation based on the provided prompt
            """
            if not self.access_key:
                raise TranslationImpossibleError(_("Access key must be set in .env or provided as an argument"))

            if not self.secret_access_key:
                raise TranslationImpossibleError(_("Secret access key must be set in .env or provided as an argument"))

            if not self.aws_region:
                raise TranslationImpossibleError(_("AWS region must be set in .env or provided as an argument"))

            if not self.model_id:
                raise TranslationImpossibleError(_("Model ID must be provided as an argument"))

            logging.debug(f"Messages:\n{FormatMessages(prompt.messages)}")

            content = _structure_messages(prompt.messages)

            reponse = self._send_messages(prompt.system_prompt, content, temperature=temperature)

            translation = Translation(reponse) if reponse else None

            return translation

        def _send_messages(self, system_prompt : str, messages : list[str], temperature : float|None = None) -> dict:
            """
            Make a request to the Amazon Bedrock API to provide a translation
            """
            if self.aborted:
                return None

            try:
                inference_config = {
                        'temperature' : temperature or 0.0,
                        'maxTokens' : self.max_tokens
                    }

                if self.supports_system_prompt and system_prompt:
                    result = self.client.converse(
                        modelId=self.model_id,
                        messages=messages,
                        system = [{ 'text' : system_prompt }],
                        inferenceConfig = inference_config
                        )
                else:
                    result = self.client.converse(
                        modelId=self.model_id,
                        messages=messages,
                        inferenceConfig = inference_config
                        )

                if self.aborted:
                    return None

                output = result.get('output')

                if not output:
                    raise TranslationResponseError(_("No output returned in the response"), response=result)

                response = {}

                if 'stopReason' in result:
                    response['finish_reason'] = result['stopReason']

                if 'usage' in result:
                    response['prompt_tokens'] = result['usage'].get('inputTokens')
                    response['output_tokens'] = result['usage'].get('outputTokens')
                    response['total_tokens'] = result['usage'].get('totalTokens')

                message = output.get('message')
                if message and message.get('role') == 'assistant':
                    text = [ content.get('text') for content in message.get('content',[]) ]
                    response['text'] = '\n'.join(text)

                # Return the response if the API call succeeds
                return response

            except Exception as e:
                raise TranslationImpossibleError(_("Error communicating with Bedrock: {error}").format(
                    error=str(e)
                ), error=e)

except ImportError:
    logging.debug("AWS Boto3 SDK not installed.")