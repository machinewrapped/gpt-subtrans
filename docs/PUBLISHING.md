# Publishing to PyPI

This document is for maintainers who want to publish the package to PyPI.

## Prerequisites

1. Install Poetry:
   ```bash
   pip install poetry
   ```

2. Configure PyPI credentials:
   ```bash
   poetry config pypi-token.pypi your-pypi-token
   ```

## Building the Package

```bash
# Build the package
poetry build

# Check the package
poetry check
```

## Publishing

```bash
# Publish to PyPI
poetry publish

# Or test on TestPyPI first
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry publish -r testpypi
```

## Version Management

Update the version in `pyproject.toml` and `PySubtitle/version.py` before publishing:

```toml
[tool.poetry]
version = "1.1.3"  # Update this
```

```python
__version__ = "v1.1.3"  # Update this too
```

## Testing the Published Package

After publishing, test the installation:

```bash
# Test basic installation
pip install gpt-subtrans

# Test with extras
pip install gpt-subtrans[all]

# Run the test suite
python tests/test_package.py
```