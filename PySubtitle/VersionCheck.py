import os
import datetime
import logging
import requests
import appdirs

from PySubtitle.version import __version__

repo_name = "gpt-subtrans"
repo_owner = "machinewrapped"

config_dir = appdirs.user_config_dir("GPTSubtrans", "MachineWrapped", roaming=True)
last_check_file = os.path.join(config_dir, 'last_check.txt')

def CheckIfUpdateAvailable():
    try:
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        response = requests.get(url)

        if response.status_code == 200:
            with open(last_check_file, "w") as f:
                f.write(datetime.date.today().isoformat())

            latest_version = response.json()["tag_name"]
            
            if latest_version != __version__:
                logging.info(f"A new version ({latest_version}) of {repo_name} is available!")
                return True

            else:
                logging.debug(f"You have the latest version ({__version__}) of {repo_name}.")
        else:
            logging.debug(f"Failed to get latest release of {repo_name}. Error: {response.status_code}")

    except Exception as e:
        logging.debug(f"Unable to check if an update is available: {str(e)}")

    return False

def CheckIfUpdateCheckIsRequired():
    try:
        with open(last_check_file, "r") as f:
            last_check = datetime.date.fromisoformat(f.read().strip())

        return datetime.date.today() > last_check

    except FileNotFoundError:
        return True
