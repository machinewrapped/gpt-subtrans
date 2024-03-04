# GPT-Subtrans
GPT-Subtrans is an open source subtitle translator that uses LLMs as a translation service. It can translate subtitles between any language pairs supported by the language model. 

Note: GPT-Subtrans requires an active internet connection. Subtitles are sent to the provider's servers for translation, so their privacy policy applies.

## Installation
For most users the packaged release is the easiest way to use the program. Simply unzip to a folder and run `gui-subtrans.exe`. You will be prompted for some basic settings on first run.

### OpenAI
https://openai.com/policies/privacy-policy

You will need an OpenAI API key from https://platform.openai.com/account/api-keys to use OpenAI's GPT models as a translator.

If the API key is associated with a free trial account the translation speed will be severely restricted.

### Google Gemini
https://ai.google.dev/terms

**Please note that the Google Gemini API can only be accessed from IP addresses in certain geographic regions: https://ai.google.dev/available_regions**

You will need a Google Gemini API key from https://ai.google.dev/ or from a project created on https://console.cloud.google.com/. You must ensure that Generative AI is enabled for the api key and project.

Gemini support is new and should be considered experimental.

### MacOS
Building MacOS universal binaries with PyInstaller has not worked for some time so releases are only provided for Apple Silicon. If you have an Intel Mac you will need to install from source to use the program. If anybody would like to volunteer to maintain Intel releases, please get in touch.

### Installing from source
For other platforms, or if you want to modify the program, you will need to have Python 3.10+ and pip installed on your system, then follow these steps.

1. Clone the GPT-Subtrans repository onto your local machine using the following command:
```
    git clone https://github.com/machinewrapped/gpt-subtrans.git
```

**The easiest setup method for most users is to run `install-openai.bat` or `install-gemini.bat` at this point and enter your API key when prompted. You can then skip the remaining steps. MacOS users should run `install-mac.sh`, which will configure OpenAI as the provider. **

2. Create a new file named .env in the root directory of the project. Add your API key to the .env file like this:
```
    OPENAI_API_KEY=<your_openai_api_key>
    GEMINI_API_KEY=<your_gemini_api_key>
```

3. Create a virtual environment for the project by running the following command in the root folder to create a local environment for the Python interpreter.:
```
    python -m venv envsubtrans
```

4. Activate the virtual environment by running the appropriate command for your operating system:
```
    .\envsubtrans\Scripts\activate
    .\envsubtrans\bin\activate
```

5. Install the required libraries using pip by running the following command in your terminal to install the project dependencies (listed in the requirements.txt file):
```
    pip install -r requirements.txt
```

6. Install the SDKs for the provider(s) you intend to use
```
    pip install openai
    pip install google.generativeai
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

GPT-Subtrans can be used as a console command. The most basic usage is:
```
gpt-subtrans <path_to_srt_file> --target_language <target_language>
gemini-subtrans <path_to_srt_file> --target_language <target_language>
```

This will activate the virtual environment and call the translation script with default parameters. If the target language is not specified, the default is English.

Note: Remember to activate the virtual environment every time you work on the project.

It is recommended to use an IDE such as Visual Studio Code to run the program when installing from source, as this will provide more control, e.g. specifying command-line parameters in a launch.json file.

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

- `--batchthreshold`:
  Number of seconds between lines to consider starting a new batch of subtitles to translate.
  Smaller batches take longer and cost more, but introduce more sync points and reduce the scope for the AI to drift.
  This setting is ignored with the new subtitle batcher, as it batches dynamically based on the gaps between lines.

- `--minbatchsize`:
  Minimum number of lines to consider starting a new batch to send to the translator. 
  Higher values typically result in faster and cheaper translations but increase the risk of desyncs.

- `--maxbatchsize`:
  Maximum number of lines before starting a new batch is compulsory.
  This needs to take into account the token limit for the model being used, but the "optimal" value depends on many factors, so experimentation is encouraged.
  Larger batches are more cost-effective but increase the risk of the AI desynchronising, triggering expensive retries.

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

- `-m`, `--model`:
  Specify the [AI model](https://platform.openai.com/docs/models) to use for translation

### Gemini-specific arguments
- `-k`, `--apikey`:
  Your [Google Gemini API Key](https://aistudio.google.com/app/apikey). Not required if it is set in the .env file.

- `-m`, `--model`:
  Specify the [AI model](https://ai.google.dev/models/gemini) to use for translation


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

- openai, of course (https://platform.openai.com/docs/libraries/python-bindings)
- srt (https://github.com/cdown/srt)
- requests (https://github.com/psf/requests)
- regex (https://github.com/mrabarnett/mrab-regex)

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
