# LLM-Subtrans Development Guide

Uses Python 3.10+ and PySide6

## Commands
- Run all tests: `python scripts/run_tests.py`
- Run single test: `python -m unittest PySubtitle.UnitTests.test_MODULE`
- Build distribution: `./scripts/makedistro.sh` (Linux/Mac) or `scripts\makedistro.bat` (Windows)
- Install dependencies: `./install.sh` (Linux/Mac) or `install.bat` (Windows)

## Code Style
- **Naming**: PascalCase for classes and methods, snake_case for variables
- **Imports**: Standard lib → third-party → local, alphabetical within groups
- **Types**: Use type hints for parameters, return values, and class variables
- **Docstrings**: Triple-quoted concise descriptions for classes and methods
- **Error handling**: Custom exceptions, specific except blocks, input validation
- **Class structure**: Docstring → constants → init → properties → public methods → private methods
- **Threading safety**: Use locks (RLock/QRecursiveMutex) for thread-safe operations
- **Validation**: Validate inputs with helpful error messages