# SubtitleGPT
SubtitleGPT is an open source subtitle translator built with the OpenAI GPT-3 language model. It can translate subtitles between any language pairs supported by GPT-3.

## Installation
To install SubtitleGPT, you will need to have Python 3.x and pip installed on your system. I recommend using Visual Studio Code (VS Code) to run the project.

1. Clone the SubtitleGPT repository onto your local machine using the following command:

git clone https://github.com/your_username/subtitlegpt.git
Create a new file named .env in the root directory of the project.

2. Add your OpenAI API key to the .env file like this:

```
OPENAI_API_KEY=<your_api_key_here>
```

Make sure to replace <your_api_key_here> with your actual API key.

3. Create a virtual environment for the project by running the following command in your terminal:

```
python3 -m venv subtitlegpt-env
```

This will create a new folder named env that contains a copy of the Python interpreter.

4. Activate the virtual environment by running the following command:

```
source env/bin/activate
```

5. Install the required libraries using pip by running the following command in your terminal:

```
pip install -r requirements.txt
```
This will install all the dependencies listed in the requirements.txt file.

6. Once the installation is complete, open the project in VS Code or your preferred IDE to start using SubtitleGPT.

Note: Remember to activate the virtual environment every time you work on the project by running the command in step 4. To deactivate the virtual environment, run the command deactivate.

## Contributing
Contributions from the community are welcome! To contribute to SubtitleGPT, follow these steps:

Fork the repository onto your own GitHub account.

Clone the repository onto your local machine using the following command:

```
git clone https://github.com/your_username/subtitlegpt.git
```

Create a new branch for your changes using the following command:

```
git checkout -b feature/your-new-feature
```

Make your changes to the code and commit them with a descriptive commit message.

Push your changes to your forked repository.

Submit a pull request to the main SubtitleGPT repository.

## License
SubtitleGPT is licensed under the MIT License.