import logging
import time
import openai
import openai.error

from PySubtitleGPT.ChatGPTPrompt import ChatGPTPrompt
from PySubtitleGPT.ChatGPTTranslation import ChatGPTTranslation
from PySubtitleGPT.Options import Options
from PySubtitleGPT.SubtitleError import NoTranslationError, TranslationError, TranslationImpossibleError

linesep = '\n'

class ChatGPTClient:
    """
    Handles communication with OpenAI to request translations
    """
    def __init__(self, options : Options, instructions=None):
        self.options = options
        self.instructions = instructions or options.get('instructions', "")

        if not self.instructions:
            raise TranslationError("No instructions provided for the translator")

    def RequestTranslation(self, prompt : str, lines : list, context : dict):
        """
        Generate the messages to send to OpenAI to request a translation
        """
        options = self.options

        start_time = time.monotonic()

        gpt_prompt = ChatGPTPrompt(self.instructions)

        gpt_prompt.GenerateMessages(prompt, lines, context)

        logging.debug(f"Messages\n{linesep.join('{0}: {1}'.format(m['role'], m['content']) for m in gpt_prompt.messages)}")

        gpt_translation = self.SendMessages(gpt_prompt.messages)

        translation = ChatGPTTranslation(gpt_translation, gpt_prompt)

        # If a rate limit is replied ensure a minimum duration for each request
        rate_limit = options.get('rate_limit')
        if rate_limit:
            minimum_duration = 60.0 / rate_limit

            elapsed_time = time.monotonic() - start_time
            if elapsed_time < minimum_duration:
                sleep_time = minimum_duration - elapsed_time
                time.sleep(sleep_time)

        return translation

    def RequestRetranslation(self, translation : ChatGPTTranslation, errors : list[TranslationError]):
        """
        Generate the messages to send to OpenAI to request a retranslation
        """
        options = self.options
        prompt = translation.prompt

        # Trim messages after the original translation to keep tokens down
        messages = []
        for message in prompt.messages:
            messages.append(message)
            if message['role'] == 'assistant':
                break
        prompt.messages = messages

        retry_instructions = options.get('retry_instructions')

        prompt.GenerateRetryPrompt(translation.text, retry_instructions, errors)

        # Let's raise the temperature a little bit
        temperature = min(options.get('temperature', 0.0) + 0.1, 1.0)
        retranslation = self.SendMessages(prompt.messages, temperature)

        return retranslation

    def SendMessages(self, messages : list[str], temperature : float = None):
        """
        Make a request to the OpenAI API to provide a translation
        """
        options = self.options
        max_retries = options.get('max_retries', 3.0)
        backoff_time = options.get('backoff_time', 5.0)
        model = options.get('gpt_model')
        temperature = temperature or options.get('temperature', 0.0)

        translation = {}
        retries = 0

        while retries <= max_retries:
            try:
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    temperature=temperature
                )

                translation['response_time'] = getattr(response, 'response_ms', 0)

                if response.usage:
                    translation['prompt_tokens'] = getattr(response.usage, 'prompt_tokens')
                    translation['completion_tokens'] = getattr(response.usage, 'completion_tokens')
                    translation['total_tokens'] = getattr(response.usage, 'total_tokens')

                # We only expect one choice to be returned as we have 0 temperature
                if response.choices:
                    choice = response.choices[0]
                    reply = response.choices[0].message

                    translation['finish_reason'] = getattr(choice, 'finish_reason', None)
                    translation['text'] = getattr(reply, 'content', None)
                else:
                    raise NoTranslationError("No choices returned in the response", response)

                # Return the response if the API call succeeds
                return translation
            
            except openai.error.RateLimitError as e:
                retry_after = e.headers.get('x-ratelimit-reset-requests') or e.headers.get('Retry-After')
                if retry_after:
                    retry_seconds = float(retry_after.rstrip("s"))
                    logging.warning(f"Rate limit hit, retrying in {retry_seconds} seconds...")
                    time.sleep(retry_seconds)
                    continue
                else:
                    logging.warning("Rate limit hit, quota exceeded. Please wait until the quota resets.")
                    raise

            except (openai.error.APIConnectionError, openai.error.Timeout, openai.error.ServiceUnavailableError) as e:
                if isinstance(e, openai.error.APIConnectionError) and not e.should_retry:
                    raise TranslationImpossibleError(str(e))
                if retries == max_retries:
                    logging.warning(f"OpenAI failure {str(e)}, aborting after {retries} retries...")
                    raise
                else:
                    retries += 1
                    sleep_time = backoff_time * 2.0**retries
                    logging.warning(f"OpenAI error {str(e)}, retrying in {sleep_time}...")
                    time.sleep(sleep_time)
                    continue

            except Exception as e:
                raise TranslationImpossibleError(f"Unexpected error communicating with OpenAI", e)

        return None

