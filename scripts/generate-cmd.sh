#!/bin/bash

# Assigning the script name and command file name
script_name=$1.py
cmd_name=$1.sh

# Displaying the generation message
echo "Generating $cmd_name..."

# Creating a new command file with the necessary commands
echo "#!/bin/bash" > "$cmd_name"
echo "echo 'Activating virtual environment...'" >> "$cmd_name"
echo "source envsubtrans/bin/activate" >> "$cmd_name"
echo "envsubtrans/bin/python scripts/$script_name" '"$@"' >> "$cmd_name"
echo "echo 'Deactivating virtual environment...'" >> "$cmd_name"
echo "deactivate" >> "$cmd_name"

# Making the generated command script executable
chmod +x "$cmd_name"
