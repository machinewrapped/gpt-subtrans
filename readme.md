# GPT-Subtrans
GPT-Subtrans is an open source subtitle translator that uses LLMs as a translation service. It can translate subtitles between any language pairs supported by the language model.

Note: GPT-Subtrans requires an active internet connection. Subtitles are sent to the provider's servers for translation, so their privacy policy applies.

## Installation
For most users the packaged release is the easiest way to use the program. Simply unzip to a folder and run `gui-subtrans.exe`. You will be prompted for some basic settings on first run.

### OpenAI
https://openai.com/policies/privacy-policy

You will need an OpenAI API key from https://platform.openai.com/account/api-keys to use OpenAI's GPT models as a translator.

If the API key is associated with a free trial account the translation speed will be severely restricted.

You can use the custom api_base parameter to access a custom OpenAI instance or other models with a compatible API, e.g. locally hosted models.

You can use an **OpenAI Azure** installation as a translation provider, but this is only advisable if you know what you're doing - in which case hopefully it will be clear how to configure the Azure provider settings. The Azure integration uses OpenAI's client library, so no additional installation is required.

### Google Gemini
https://ai.google.dev/terms

**Please note that the Google Gemini API can only be accessed from IP addresses in certain geographic regions: https://ai.google.dev/available_regions**

You will need a Google Gemini API key from https://ai.google.dev/ or from a project created on https://console.cloud.google.com/. You must ensure that Generative AI is enabled for the api key and project.

### Anthropic Claude
https://support.anthropic.com/en/collections/4078534-privacy-legal

You will need an Anthropic API key from https://console.anthropic.com/settings/keys to use Claude as a provider. The Anthropic SDK does not provide a way to retrieve available models, so the latest Claude 3 model names are currently hardcoded in the GUI. Only the smallest Haiku model has been tested - it seems more than adequate for translation tasks.

The API has very strict [rate limits](https://docs.anthropic.com/claude/reference/rate-limits) based on your credit tier, both on requests per minutes and tokens per day. The free credit tier limits should be sufficient to translate approximately one full movie per day.

Claude support is new and should be considered experimental.

### Local Server
GPT-Subtrans can interface with a locally hosted server which supports an OpenAI compatible API, e.g. [LM Studio](https://lmstudio.ai/). This is mainly for research and experimentation, and you should not expect particularly good results. LLMs like GPT and Gemini derive much of their power from their size, and small, quantized models running locally are likely to produce poor translations, fail to generate valid responses that follow instructions and frequently get stuck in endless generation loops. If you find a model that can run locally and reliably produces good results, please post about your experience in the Discussions area!

Chat and completion endpoints are supported, you should configure the settings and endpoint based on the model the server is running (e.g. instruction tuned models will probably produce better results using the completions endpoint rather than chat/conversation). The prompt template can be edited in the GUI - make sure to include at least the {prompt} tag in the template, as this is where the subtitles that need translating in each batch will be provided.

### MacOS
Building MacOS universal binaries with PyInstaller has not worked for some time so releases are only provided for Apple Silicon. If you have an Intel Mac you will need to install from source to use the program. If anybody would like to volunteer to maintain Intel releases, please get in touch.

### Linux
Prebuilt Linux packages are not provided so you will need to install from source.

### Installing from source
For other platforms, or if you want to modify the program, you will need to have Python 3.10+ and pip installed on your system, then follow these steps.

#### step1

1. Clone the GPT-Subtrans repository onto your local machine using the following command:
```
    git clone https://github.com/machinewrapped/gpt-subtrans.git
```

The easiest setup method for most users is to run an installation script, e.g. `install-openai.bat` or `install-gemini.bat` at this point and enter your API key when prompted. This will create a virtual environment and install all the required packages for the provider, and generate command scripts to launch the specified provider. You can then skip the remaining steps.

MacOS and Linux users should run `install.sh` instead (this should work on any unix-like system).

During the installing process, input the apikey you have, and the .env file will be created automatically. Thus, you can ignore step2, but you are recommended to read it.

#### step2

2. Create a new file named .env in the root directory of the project. Add any required settings for your chosen provider to the .env file like this:
```
    OPENAI_API_KEY=<your_openai_api_key>
    GEMINI_API_KEY=<your_gemini_api_key>
    AZURE_API_KEY=<your_azure_api_key>
    CLAUDE_API_KEY=<your_claude_api_key>
```

If you are using Azure:

```
AZURE_API_BASE=<your api_base, such as https://something.openai.azure.com>
AZURE_DEPLOYMENT_NAME=<deployment_name>
```
#### step3

3. Create a virtual environment for the project by running the following command in the root folder to create a local environment for the Python interpreter.:
```
    python -m venv envsubtrans
```

notice： For linux user, the environment has already prepared during the installing process.

#### step4

4. Activate the virtual environment by running the appropriate command for your operating system:
```
    .\envsubtrans\Scripts\activate
    .\envsubtrans\bin\activate
    soure path/to/gpt-subtrans/envsubtrans/bin/activate    # for linux user
```

#### step5

5. Install the required libraries using pip by running the following command in your terminal to install the project dependencies (listed in the requirements.txt file):
```
    pip install -r requirements.txt
```

#### step6

6. Install the SDKs for the provider(s) you intend to use
```
    pip install openai
    pip install google.generativeai
    pip install anthropic
```

Note that steps 3 and 4 are optional, but they can help prevent conflicts with other Python applications.

## Usage
The program works by dividing the subtitles up into small batches and sending each one to the translation service in turn. It is likely to take time to complete, and can potentially make many API calls for each subtitle file.

By default The translated subtitles will be written to a new SRT file in the same directory with the target langugage appended to the original filename.

It is highly recommended to use Subtitle Edit's (https://www.nikse.dk/subtitleedit) "Fix Common Errors" to clean up the translated subtitles (e.g. to add line breaks).

### GUI
For most people the [Subtrans GUI](https://github.com/machinewrapped/gpt-subtrans/wiki/GUI#gui-subtrans) is the best and easiest way to use the program. After installation, launch the GUI with the `gui-subtrans` command or shell script, and hopefully the rest should be self-explanatory.

See the project wiki for further details on how to use the program.

### Command Line

Before use these scripts, you need to change directory to scripts folder and activate the environment.
GPT-Subtrans can be used as a console command or shell script. The most basic usage is:
```
gpt-subtrans <path_to_srt_file> --target_language <target_language>
gemini-subtrans <path_to_srt_file> --target_language <target_language>
claude-subtrans <path_to_srt_file> --target_language <target_language>
llm-subtrans -s <server_address> -e <endpoint> -l <language> <path_to_srt_file>
python3 batch_process.py  # process files in different folders
```

This will activate the virtual environment and call the translation script with default parameters. If the target language is not specified the default is English.

### Proxy

If you need to use proxy in your location, you can use socks proxy by using command line

```
python3 gpt-subtrans.py <path_to_srt_file> --target_language <target_language> --proxy socks://127.0.0.1:1089
```
Remember to change the local port to yours and turn on your proxy tools such as v2ray, naiveproxy and clash.

### batch process

you can process files with the following struct：

      #   -SRT
      #   --fold1
      #   ---1.srt
      #   ---2.srt
      #   ...
      #   --fold2
      #   ---1.srt
      #   ---2.srt
      #   ...

```
python3 batch_process.py  # process files in different folders
```
You need to modify the command line in batch_process.py accordingly


### Developers
It is recommended to use an IDE such as Visual Studio Code to run the program when installed from source, and set up a launch.json file to specify the arguments.

Note: Remember to activate the virtual environment every time you work on the project.

## Advanced usage

There are a number of command-line arguments that offer more control over the translation process.

Default values for many settings can be set in the .env file, using a NAME_IN_CAPS with format. See Options.py for the full list.

To use any of these arguments, add them to the command-line after the path to the SRT file. For example:

```
gpt-subtrans path/to/my/subtitles.srt --moviename "My Awesome Movie" --ratelimit 10 --substitution cat::dog
```

- `-l`, `--target_language`:
  The language to translate the subtitles to.

- `-o`, `--output`:
  Specify a filename for the translated subtitles.

- `--project`:
  Read or Write a project file for the subtitles being translated. More on this below.

- `--ratelimit`:
  Maximum number of requests to the translation service per minute (mainly relevant if you are using an OpenAI free trial account).

- `--moviename`:
  Optionally identify the source material to give context to the translator.

- `--description`:
  A brief description of the source material to give further context. Less is generally more here, or the AI can start improvising.

- `--name`, `--names`:
  Optionally provide (a list of) names to use in the translation (more powerful AI models are more likely to actually use them).

- `--substitution`:
  A pair of strings separated by `::`, to substitute in either source or translation, or the name of a file containing a list of such pairs.

- `--scenethreshold`:
  Number of seconds between lines to consider it a new scene.

- `--minbatchsize`:
  Minimum number of lines to consider starting a new batch to send to the translator.
  Higher values typically result in faster and cheaper translations but increase the risk of desyncs.

- `--maxbatchsize`:
  Maximum number of lines before starting a new batch is compulsory.
  This needs to take into account the token limit for the model being used, but the "optimal" value depends on many factors, so experimentation is encouraged.
  Larger batches are more cost-effective but increase the risk of the AI desynchronising, triggering expensive retries.

- `--preprocess`:
  Preprocess the subtitles prior to batching.
  This performs various actions to prepare the subtitles for more efficient translation, e.g. splitting long (duration) lines into multiple lines.
  Mainly intended for subtitles that have been automatically transcribed with e.g. Whisper.

- `--postprocess`:
  Post-process translated subtitles.
  Performs various actions like adding line breaks to long lines and normalising dialogue tags after a translation request.

- `--instruction`:
  An additional instruction for the AI indicating how it should approach the translation.

- `--instructionfile`:
  Name/path of a file to load AI system instructions from (otherwise the default instructions.txt is used).

- `--maxlines`:
  Maximum number of batches to process. To end the translation after a certain number of lines, e.g. to check the results.

- `--temperature`:
  A higher temperature increases the random variance of translations. Default 0.

### OpenAI-specific arguments
- `-k`, `--apikey`:
  Your [OpenAI API Key](https://platform.openai.com/account/api-keys). Not required if it is set in the .env file.

- `-b`, `--apibase`:
  API base URL if you are using a custom instance. if it is not set, the default URL will be used.

- '--httpx':
  Use the [HTTPX library](https://github.com/projectdiscovery/httpx) for requests (only supported if apibase is specified)

- `-m`, `--model`:
  Specify the [AI model](https://platform.openai.com/docs/models) to use for translation

### Gemini-specific arguments
- `-k`, `--apikey`:
  Your [Google Gemini API Key](https://aistudio.google.com/app/apikey). Not required if it is set in the .env file.

- `-m`, `--model`:
  Specify the [AI model](https://ai.google.dev/models/gemini) to use for translation

### Claude-specific arguments
- `-k`, `--apikey`:
  Your [Anthropic API Key](https://console.anthropic.com/settings/keys). Not required if it is set in the .env file.

- `-m`, `--model`:
  Specify the [AI model](https://docs.anthropic.com/claude/docs/models-overview#model-comparison) to use for translation. This should be the full model name, e.g. `claude-3-haiku-20240307`

### Local Server specific arguments
- `-s`, `--server`:
  The address the server is running on, including port (e.g. http://localhost:1234). Should be provided by the server

- `-e`, `--endpoint`:
  The API function to call on the server, e.g. `/v1/completions`. Choose an appropriate endpoint for the model running on the server.

- `--chat`:
  Specify this argument if the endpoint expects requests in a conversation format - otherwise it is assumed to be a completion endpoint.

- `--systemmessages`:
  If using a conversation endpoint, translation instructions will be sent as the "system" user if this flag is specified.

- `-k`, `--apikey`:
  Local servers shouldn't need an api key, but the option is provided in case it is needed for your setup.

- `-m`, `--model`:
  The model will usually be determined by the server, but the option is provided in case you need to specify it.

## Project File

**Note** If you are using the GUI a project file is created automatically when you open a subtitle file for the first time, and updated automatically.

The `--project` argument or `PROJECT` .env setting can take a number of values, which control whether and when an intermediate file will be written to disc.

The default setting is `None`, which means the project file is neither written nor read, the only output of the program is the final translation.

If the argument is set to `True` then a project file will be created with the `.subtrans` extension, containing details of the translation process,
and it will be updated as the translation progresses. Writing a project file allows, amongst other things, resuming a translation that was interrupted.

Other valid options include `preview`, `resume`, `reparse` and `retranslate`. These are probably only useful if you're modifying the code, in which case
you should be able to see what they do.

## Version History

Version 0.6 changes the architecture to a provider-based system, allowing multiple AI services to be used as translators.
Settings are compartmentalised for each provider. For the intial release the only supported provider is **OpenAI**.

Version 0.5 adds support for gpt-instruct models and a refactored code base to support different translation engines. For most users, the recommendation is still to use the **gpt-3.5-turbo-16k** model with batch sizes of between (10,100) lines, for the best combination of performance/cost and translation quality.

Version 0.4 features significant optimisations to the GUI making it more responsive and usable, along with numerous bug fixes.

Version 0.3 featured a major effort to bring the GUI up to full functionality and usability, including adding options dialogs and more, plus many bug fixes.

Version 0.2 employs a new prompting approach that greatly reduces desyncs caused by GPT merging together source lines in the translation. This can reduce the naturalness of the translation when the source and target languages have very different grammar, but it provides a better base for a human to polish the output.

The instructions have also been made more detailed, with multiple examples of correct output for GPT to reference, and the generation of summaries has been improved so that GPT is better able to understand the context of the batch it is translating. Additionally, double-clicking a scene or batch now allows the summary to be edited by hand, which can greatly improve the results of a retranslation and of subsequent batches or scenes. Individually lines can also be edited by double-clicking them.

## Contributing
Contributions from the community are welcome! To contribute, follow these steps:

Fork the repository onto your own GitHub account.

Clone the repository onto your local machine using the following command:

```
git clone https://github.com/your_username/GPT-Subtrans.git
```

Create a new branch for your changes using the following command:

```
git checkout -b feature/your-new-feature
```

Make your changes to the code and commit them with a descriptive commit message.

Push your changes to your forked repository.

Submit a pull request to the main GPT-Subtrans repository.

## Acknowledgements
This project uses several useful libraries:

- srt (https://github.com/cdown/srt)
- requests (https://github.com/psf/requests)
- regex (https://github.com/mrabarnett/mrab-regex)
- httpx (https://github.com/projectdiscovery/httpx)

Translation providers:
- openai (https://platform.openai.com/docs/libraries/python-bindings)
- google.generativeai (https://github.com/google/generative-ai-python)
- anthropic (https://github.com/anthropics/anthropic-sdk-python)

For the GUI:
- pyside6 (https://wiki.qt.io/Qt_for_Python)
- events (https://pypi.org/project/Events/)
- darkdetect (https://github.com/albertosottile/darkdetect)
- appdirs (https://github.com/ActiveState/appdirs)

For bundled versions:
- python (https://www.python.org/)
- pyinstaller (https://pyinstaller.org/)

## License
GPT-Subtrans is licensed under the MIT License. See LICENSE for the 3rd party library licenses.
