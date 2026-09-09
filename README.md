# Guppy FT

Guppy FT is an extension of the [Guppy](https://github.com/Quantinuum/guppylang) quantum programming language to aid
with writing, compiling and running fault-tolerant quantum programs. As a toolkit, it provides:

- A framework to define QEC architectures
- Transformations through quantum program abstraction layers: From computational to logical to physical
- Verification tools to validate QEC primitive implementations

Together, this enables automatic encoding of arbitrary Guppy programs, including measurement dependent control flow.

```python
from guppylang import guppy
from guppylang.std.builtins import owned, output
from guppylang.std.quantum import cx, h, measure, qubit, x, z
from guppyft.code.steane.encode import SteaneBuilder


@guppy
def teleport() -> None:
    """Teleports the state in `src` to `tgt`."""
    src = qubit()

    tmp = qubit()
    tgt = qubit()
    h(tmp)
    cx(tmp, tgt)

    cx(src, tmp)
    h(src)
    if measure(src).read():
        z(tgt)
    if measure(tmp).read():
        x(tgt)

    output("tgt", measure(tgt).read())


# Use Steane architecture to encode the program
steane = SteaneBuilder().build(n_blocks=3)
teleport_encoded = steane.encode(teleport.compile())
```

## Documentation

📖 [Getting Started][docs]

📒 [Example notebooks][examples]

[examples]: ./examples/
[docs]: https://docs.quantinuum.com/guppy/ft

## Installation

Guppy FT can be installed from [PyPI](https://pypi.org/project/guppyft/) using `pip`. Requires Python>=3.12.

```bash
pip install guppyft
```

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for instructions on setting up the development environment.

## Licence

This project is licensed under Apache License, Version 2.0 ([LICENCE][]
or <http://www.apache.org/licenses/LICENSE-2.0>).

[LICENCE]: ./LICENCE
