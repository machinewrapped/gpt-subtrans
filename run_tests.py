import os
import logging
import importlib.util

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler and set level to info
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
console.setFormatter(formatter)
logger.addHandler(console)


def run_all_tests(tests_directory, subtitles_directory, results_directory):
    """
    Scans the given directory for .py files, imports them, and runs the run_tests function if it exists.
    :param tests_directory: Directory containing the test .py files.
    :param subtitles_directory: Path to test_subtitles subdirectory.
    """
    # List all files in the tests directory
    for filename in os.listdir(tests_directory):
        if not filename.endswith('.py') or filename.startswith('__init__'):
            continue

        module_name = filename[:-3]  # Remove ".py" from filename to get module name

        # Create the absolute file path
        filepath = os.path.join(tests_directory, filename)

        # Load the module
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Check if run_tests function exists
        if hasattr(module, 'run_tests'):
            module.run_tests(subtitles_directory, results_directory)

if __name__ == "__main__":
    root_directory = os.path.dirname(os.path.abspath(__file__))
    tests_directory = os.path.join(root_directory, 'Tests')
    subtitles_directory = os.path.join(root_directory, 'test_subtitles')
    results_directory =  os.path.join(root_directory, 'test_results')
    
    if not os.path.exists(results_directory):
        os.makedirs(results_directory)

    run_all_tests(tests_directory, subtitles_directory, results_directory)
