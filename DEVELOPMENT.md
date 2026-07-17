# Welcome to the guppyft development guide <!-- omit in toc -->

This guide is intended to help you get started with developing guppylang.

If you find any errors or omissions in this document, please [open an issue](https://github.com/quantinuum-dev/guppyft/issues/new)!

# 🌐 Contributing to guppyft

> [!NOTE]
> By submitting a contribution to this project, you certify that you have the right to submit it and agree that your contribution is licensed under the Apache License, Version 2.0, under the same terms as the rest of the project.

Contributions to guppyft are welcomed! Please open [an issue](https://github.com/quantinuum-dev/guppyft/issues/new) or [pull request](https://github.com/quantinuum-dev/guppyft/compare) if you have any questions or suggestions.

PRs should be made against the `main` branch, and should pass all CI checks before being merged. This includes using the [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) format in the PR title.

## #️⃣ Setting up the development environment

To set up the development environment, you will need:

- `uv`: <https://docs.astral.sh/uv/getting-started/installation/>
- `just`: <https://just.systems/man/en/installation.html>
- `rust`: <https://www.rust-lang.org/tools/install>
- `cargo-nextest`: <https://nexte.st/docs/installation/pre-built-binaries/>

Once installed, you can install all Python dependencies and enable the pre-commit hooks by running:

```bash
just setup
```

To see a list of all available commands, run:

```bash
just
```

## 💅 Coding style

The Python code in this repository is formatted using [ruff](https://docs.astral.sh/ruff/) and the Rust code using [rustfmt](https://github.com/rust-lang/rustfmt) to ensure a consistent style.
Most IDEs will provide automatic formatting on save, but you can also run the formatter manually with:

```bash
just format
```

We also use various linters to catch common mistakes and enforce best practices. To run these, use:

```bash
just check
```

To quickly fix some common issues, run:

```bash
just fix
```

This may not be able to fix all issues, and some manual inspection will be required to address any outstanding errors.

## 🏃 Running the tests

To quickly compile and run all the tests, you can use:

```bash
just test
```

To run only the Rust or Python tests, use:
```bash
just test-rust
just test-python
```
