# LLM-Subtrans Development Guide

Uses Python 3.10+ and PySide6. 
Never import or use outdated typing members like List and Union.

Secrets are stored in a .env file - you must never read the contents of the file.

## Commands
- Run all tests: `python scripts/run_tests.py`
- Run single test: `python -m unittest PySubtitle.UnitTests.test_MODULE`
- Build distribution: `./scripts/makedistro.sh` (Linux/Mac) or `scripts\makedistro.bat` (Windows)
- Install dependencies: `./install.sh` (Linux/Mac) or `install.bat` (Windows)

## Code Style
- **Naming**: PascalCase for classes and methods, snake_case for variables
- **Imports**: Standard lib → third-party → local, alphabetical within groups
- **Types**: Use type hints for parameters, return values, and class variables
- **Type Hints**: 
  - **CRITICAL**: Do NOT put spaces around the `|` in type unions. Use `str|None`, never `str | None`
  - DO put spaces around the colon introducing a type hint: `def func(param : str) -> bool:`
  - Examples: `def get_value(self) -> str|None:` ✅ `def get_value(self) -> str | None:` ❌
- **Docstrings**: Triple-quoted concise descriptions for classes and methods
- **Error handling**: Custom exceptions, specific except blocks, input validation
- **Class structure**: Docstring → constants → init → properties → public methods → private methods
- **Threading safety**: Use locks (RLock/QRecursiveMutex) for thread-safe operations
- **Validation**: Validate inputs with helpful error messages