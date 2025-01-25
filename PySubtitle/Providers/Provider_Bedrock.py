import logging
import os

try:
    import boto3

    from PySubtitle.Providers.Bedrock.BedrockClient import BedrockClient
    from PySubtitle.TranslationClient import TranslationClient
    from PySubtitle.TranslationProvider import TranslationProvider
    from PySubtitle.Helpers import GetEnvFloat

    class BedrockProvider(TranslationProvider):
        name = "Bedrock"

        information = """
        <p>Bedrock API provider.</p>
        <p>To use Bedrock as a provider you need to provide an access key and secret access key. These can be set up in the AWS IAM console.</p>
        <p>You must also specify an AWS region to use for requests - this will affect model availability.</p>
        """

        def __init__(self, settings : dict):
            super().__init__(self.name, {
                "access_key": settings.get('access_key', os.getenv('AWS_ACCESS_KEY_ID')),
                "secret_access_key": settings.get('secret_access_key', os.getenv('AWS_SECRET_ACCESS_KEY')),
                "aws_region": settings.get('aws_region', os.getenv('AWS_REGION', 'eu-west-1')),
                "model": settings.get('model', 'Amazon-Titan-Text-G1'),
                'temperature': settings.get('temperature', 0.0),
                "rate_limit": settings.get('rate_limit', None)
            })

            self.refresh_when_changed = ['access_key', 'secret_access_key', 'aws_region']

        @property
        def access_key(self):
            return self.settings.get('access_key')

        @property
        def secret_access_key(self):
            return self.settings.get('secret_access_key')

        @property
        def aws_region(self):
            return self.settings.get('aws_region')

        def GetTranslationClient(self, settings : dict) -> TranslationClient:
            client_settings = self.settings.copy()
            client_settings.update(settings)
            client_settings.update({
                'supports_conversation': True,
                'supports_system_messages': False,
                'supports_system_prompt': False             # Apparently some models do?
                })
            return BedrockClient(client_settings)

        def GetOptions(self) -> dict:
            options = {
                'access_key': (str, "An AWS access key is required"),
                'secret_access_key': (str, "The AWS region to use for requests must be specified."),
                'aws_region': (str, "An AWS secret access key is required"),
            }

            if self.access_key and self.secret_access_key and self.aws_region:
                models = self.available_models or ["Unable to retrieve model list"]
                options.update({
                    'model': (models, "AI model to use as the translator"),
                    'rate_limit': (float, "The maximum number of requests to make per minute")
                })
            return options

        def GetInformation(self) -> str:
            information = self.information
            if not self.ValidateSettings():
                information = information + f"<p>{self.validation_message}</p>"
            return information

        def GetAvailableModels(self) -> list[str]:
            """
            Returns a list of possible values for the model
            """
            try:
                if not self.access_key or not self.secret_access_key:
                    logging.debug("AWS access keys not provided")
                    return []

                client = boto3.client(
                    'bedrock',
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_access_key,
                    region_name=self.aws_region
                )

                response = client.list_foundation_models()

                if not response or 'modelSummaries' not in response:
                    return []

                model_details = response['modelSummaries']

                # Define valid statuses for filtering
                valid_status = ['ACTIVE','AVAILABLE']

                # Filter for translation models that are in the valid statuses
                translation_models = [
                    model['modelId']
                    for model in model_details
                        if 'TEXT' in model.get('inputModalities', []) and model.get('modelLifecycle', []).get('status') in valid_status
                ]

                # If no translation-specific models are available, fall back to all available models
                model_list = translation_models or [ model['modelId'] for model in model_details]

                # Return sorted list of model IDs
                return sorted(model_list)

            except Exception as e:
                logging.error(f"Unable to retrieve available AI models: {str(e)}")
                return []

        def ValidateSettings(self) -> bool:
            """
            Validate the settings for the provider
            """
            if not self.access_key:
                self.validation_message = "AWS access key is required"
                return False

            if not self.secret_access_key:
                self.validation_message = "AWS secret access key is required"
                return False

            if not self.aws_region:
                self.validation_message = "AWS region is required"
                return False

            return True

        def _allow_multithreaded_translation(self) -> bool:
            """
            Assume the Bedrock provider can handle multiple requests
            """
            return True

except ImportError:
    logging.info("Amazon Boto3 SDK is not installed. Bedrock provider will not be available")
