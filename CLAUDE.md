# FastAPI IP Allowlist Middleware Development Guide

## Commands
- Setup: `pip install -e '.[dev]'`
- Run tests: `pytest`
- Run single test: `pytest tests/test_file.py::test_function -v`
- Lint: `ruff check .`
- Format: `yapf -i --style=pep8 --line-length=79 *.py`
- Type check: `mypy .`

## Code Style Guidelines
- Follow PEP-8 with 79 character line limit
- Use Python type hints throughout
- Use single quotes for strings, double quotes only for docstrings
- Import order: stdlib → third-party → local, alphabetized
- Naming: snake_case for functions/variables, CamelCase for classes
- Use f-strings for string formatting
- Raise specific exceptions with descriptive messages
- Write descriptive docstrings (Google style)
- 100% test coverage for core functionality
- Handle all expected exceptions gracefully
- Use async/await patterns consistently with FastAPI
- Use the Python unittest framework for the tests themselves
