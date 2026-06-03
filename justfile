set shell := ["bash", "-uc"]

# List the available commands
help:
    @just --list --justfile {{ justfile() }}

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
    uv run cargo nextest r --all-features {{TEST_ARGS}}

# Run the Python tests.
test-python *PYTEST_FLAGS:
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
