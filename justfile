set shell := ["bash", "-uc"]

# List the available commands
help:
    @just --list --justfile {{ justfile() }}

# Prepare the development environment by installing all dependencies and enable pre-commit hooks.
setup:
    uv sync --all-extras
    [[ -n "${JUST_INHIBIT_GIT_HOOKS:-}" ]] || uv run pre-commit install -t pre-commit

# Run the pre-commit checks.
check:
    uv run pre-commit run --all-files

_check_nextest_installed:
    #!/usr/bin/env bash
    cargo nextest --version >/dev/null 2>&1 || { echo "❌ cargo-nextest not found. Install binary from https://nexte.st/docs/installation/pre-built-binaries/"; exit 1; }

# Run the Rust and Python tests.
test: test-rust test-python

# Run the Rust tests.
test-rust *TEST_ARGS: _check_nextest_installed
    uv run cargo nextest r --workspace --exclude guppyft-bindings --all-features {{ TEST_ARGS }}

# Run the Python tests.
test-python *PYTEST_FLAGS:
    uv run pytest -n auto {{ PYTEST_FLAGS }}

# Auto-fix lint issues that Ruff can safely rewrite.
fix:
    uv run ruff check --fix

# Format the Python code with Ruff.
format:
    uv run ruff format

# Generate serialized declarations for the HUGR extensions
gen-extensions:
    cargo run -p extensions gen-extensions -o src/guppyft/extensions/data --unversioned
