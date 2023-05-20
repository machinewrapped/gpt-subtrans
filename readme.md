# GPT-Subtrans
GPT-Subtrans is an open source subtitle translator built with OpenAI's ChatGPT. It can translate subtitles between any language pairs supported by the GPT language model. You will need an OpenAI API key from https://platform.openai.com/account/api-keys to use the translator. If you are on the free trial the speed will be severely restricted.

Note: GPT-Subtrans requires an active internet connection to access the OpenAI API. Subtitles are sent to OpenAI's servers for translation, so their privacy policy applies: https://openai.com/policies/privacy-policy.

## New
Added a settings dialog for the GUI. Use the somewhat inappropriate icon with four dots on the toolbar to access it. If anybody would like to volunteer to create & add proper icons to the GUI, it would be a great contribution.

## Installation
For most users the packaged release is the easiest way to use the program. Simply unzip to a folder and run `gui-subtrans.exe`. You will be prompted for some basic settings on first-run.

### Source code installation
For other platforms, or if you want to modify the program, you will need to have Python 3.x and pip installed on your system, then follow these steps.

1. Clone the GPT-Subtrans repository onto your local machine using the following command:
```
    git clone https://github.com/machinewrapped/gpt-subtrans.git
```

**The easiest setup method for most users is to run `install.bat` or `install.sh` and enter your OpenAI API key when prompted. You can then skip the remaining steps.**

2. Create a new file named .env in the root directory of the project. Add your OpenAI API key to the .env file like this:
```
    API_KEY=<your_api_key_here>
```

3. Create a virtual environment for the project by running the following command in the root folder to create a local environment for the Python interpreter.:
```
    python -m venv envsubtrans
```

4. Activate the virtual environment by running the following command:
```
    .\envsubtrans\Scripts\activate
```

5. Install the required libraries using pip by running the following command in your terminal to install the project dependencies (listed in the requirements.txt file):
```
    pip install -r requirements.txt
```

Note that steps 3 and 4 are optional, but they can help prevent conflicts with other Python applications.

## Usage

### GUI

The easiest way for most people to use GPT-Subtrans is with the [Subtrans GUI](https://github.com/machinewrapped/gpt-subtrans/wiki/GUI#gui-subtrans). After installation launch the GUI with the `gui-subtrans` command or shell script, and in theory the rest should be self-explanatory. In practise it almost certainly is not, so I'll work on documenting and improving the interface.

### Command Line

GPT-Subtrans can still be used as a console command for scripting, or if that's what you prefer. The most basic usage is:
```
gpt-subtrans <path_to_srt_file> --target_language <target_language>
```

This will activate the virtual environment and call the translation script with default parameters. If the target language is not specified, the default is English.

Note: Remember to activate the virtual environment every time you work on the project.

The program works by dividing the subtitles up into small batches and sending each one to Chat GPT in turn. It is likely to take a long time to complete, and can potentially make hundreds of API calls.

By default The translated subtitles will be written to a new SRT file with the suffix -ChatGPT added to the original filename, in the same directory.

For more control over the translation process it is recommended to use an IDE such as VS Code.

It is highly recommended to use Subtitle Edit's (https://www.nikse.dk/subtitleedit) "Fix Common Errors" on the results to clean them up (e.g. add line breaks).

## Advanced usage

There are a number of command-line arguments that offer more control over the translation process. Many of these work for the GUI as well as the command line, though the more common options can more easily be set in the GUI.

Many of these settings can be configured in the .env file too, using a similar name NAME_IN_CAPS with underscores, 
along with some other configuration options. See Options.py for the full list. Arguments specified on the command line have priority.


- `-o`, `--output`:
  Specify the filename for the translated subtitles.

- `-p`, `--project`:
  Read or Write a project file for the subtitles being translated. More on this below.

- `-r`, `--ratelimit`:
  Maximum number of batches per minute to process. If you're on the OpenAI free trial this to about 10.

- `-m`, `--moviename`:
  Optionally specify the name of the movie to give context to the translator.

- `--synopsis`:
  A brief synopsis of the film to give context. Less is more here, otherwise ChatGPT can start improvising.

- `-c`, `--character`, `--characters`:
  Optionally provide (a list of) character names to use in the translation.

- `-s`, `--substitution`:
  A pair of strings separated by `::`, to substitute in either source or translation, or the name of a file containing a list of such pairs.

- `--scenethreshold`:
  Number of seconds between lines to consider it a new scene.

- `--batchthreshold`:
  Number of seconds between lines to consider starting a new batch of subtitles to translate.
  Smaller batches take longer and cost more, but introduce more sync points and reduce the scope for ChatGPT to drift.

- `--minbatchsize`:
  Minimum number of lines to consider starting a new batch to send to ChatGPT. Higher values result in
  faster and cheaper translations but increase the risk of ChatGPT desyncing.

- `--maxbatchsize`:
  Maximum number of lines before starting a new batch is compulsory. Higher values make the translation
  faster and cheaper, but increase the risk of ChatGPT getting confused or improvising.

- `--maxbatchsize`:
  Maximum number of lines before starting a new batch is compulsory. Higher values make the translation
  faster and cheaper, but increase the risk of ChatGPT getting confused or improvising.

- `-k`, `--apikey`:
  Your OpenAI API Key (https://platform.openai.com/account/api-keys). Not required if it is set in .env

- `-t`, `--temperature`:
  A higher temperature increases the random variance of translations. Default 0.

- `-i`, `--instruction`:
  An additional instruction for Chat GPT about how it should approach the translation.

- `-f`, `--instructionfile`:
  Name/path of a file to load GPT instructions from (otherwise the default instructions.text is used).

- `--maxlines`:
  Maximum number of batches to process. To end the translation after a certain number of lines, e.g. to check the results.

To use any of these arguments, add them to the command-line after the path to the SRT file. For example:

```
gpt-subtrans path/to/my/subtitles.srt --moviename "My Awesome Movie" --ratelimit 10 -s cat::dog
```

## Project File

**Note** If you are using the GUI a project file is created automatically when you open a subtitle file for the first time, and the project is generally updated automatically when anything changes, so you shouldn't need to use the project argument.

The `--project` argument or `PROJECT` .env setting can take a number of values, which control whether and when an intermediate file will be written to disc.

The default setting is `None`, which means the project file is neither written nor read, the only output of the program is the final translation.

If the argument is set to `True` then a JSON file will be created with the `.subtrans` extension, containing details of the translation process, 
and it will be updated as the translation progresses.

Writing a project file allows, amongst other things, resuming a translation that was interrupted. Set the argument to `resume` to enable this.

Other valid options include `preview`, `reparse` and `retranslate`. These are probably only useful if you're modifying the code, in which case
you should be able to see what they do.


## Contributing
Contributions from the community are welcome! To contribute to GPT-Subtrans, follow these steps:

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
