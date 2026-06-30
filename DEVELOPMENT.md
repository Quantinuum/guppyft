# Welcome to the guppyft development guide <!-- omit in toc -->

This guide is intended to help you get started with developing guppylang.

If you find any errors or omissions in this document,
please [open an issue](https://github.com/quantinuum-dev/guppyft/issues/new)!

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
