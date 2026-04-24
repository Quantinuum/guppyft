set shell := ["bash", "-uc"]

# List the available commands
help:
    @just --list --justfile {{ justfile() }}

# Run the pre-commit checks.
check:
    uv run pre-commit run --all-files

# Run the tests.
test *PYTEST_FLAGS:
    uv run pytest {{ PYTEST_FLAGS }}

# Auto-fix all clippy warnings.
fix:
    uv run ruff check --fix

# Format the code.
format:
    uv run ruff format
