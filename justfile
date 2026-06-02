set shell := ["bash", "-uc"]

# List the available commands
help:
    @just --list --justfile {{ justfile() }}

# Run the pre-commit checks.
check:
    uv run pre-commit run --all-files

# Run the Python tests.
test *PYTEST_FLAGS:
    uv run pytest {{ PYTEST_FLAGS }}

# Auto-fix lint issues that Ruff can safely rewrite.
fix:
    uv run ruff check --fix

# Format the Python code with Ruff.
format:
    uv run ruff format

# Generate serialized declarations for the HUGR extensions
gen-extensions:
    cargo run -p extensions gen-extensions -o src/guppyft/extensions/data
