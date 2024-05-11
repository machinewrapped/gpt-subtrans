import os
import subprocess

# Specify the root directory path
root_dir = "/path/to/your/SRT/"   # change to your srt file directory

# Traverse all subfolders under the root directory
# the structure of flies are
#
#   -SRT
#   --fold1
#   ---1.srt
#   ---2.srt
#   ...
#   --fold2
#   ---1.srt
#   ---2.srt
#   ...

for subdir, dirs, files in os.walk(root_dir):
    for file in files:
        # Check if the file ends with '.srt'
        if file.endswith(".srt"):
            # Build the full path of the source file
            src_file = os.path.join(subdir, file)

            # Call gpt-subtrans.py for translation
            subprocess.run(
                ["python3", "/path/to/gpt-subtrans/scripts/gpt-subtrans.py", src_file, "--target_language", "Chinese",
                 "--instructionfile", "/home/kdt/gpt-subtrans/instructions/instructions (english to chinese).txt"])

            print(f"Translated: {src_file}")
