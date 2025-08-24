import logging
import os
import sys
import unittest

# Add the parent directory to the sys path so that modules can be found
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_path)

from PySubtitle.UnitTests import *
from PySubtitle.Helpers.Tests import create_logfile

from GUI.UnitTests import *

if __name__ == '__main__':
    scripts_directory = os.path.dirname(os.path.abspath(__file__))
    root_directory = os.path.dirname(scripts_directory)
    results_directory =  os.path.join(root_directory, 'test_results')

    if not os.path.exists(results_directory):
        os.makedirs(results_directory)

    logging.getLogger().setLevel(logging.INFO)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

    create_logfile(results_directory, "unit_tests.log")

    unittest.main()

