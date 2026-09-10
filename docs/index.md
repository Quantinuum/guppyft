---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
kernelspec:
  name: python3
  display_name: Python 3
---

# Guppy FT

```{toctree}
:maxdepth: 1
:hidden:

getting_started.md
architecture_dev.md
examples_index.md
api/api.md
```

Guppy FT is an extension of the [Guppy](https://github.com/Quantinuum/guppylang) quantum programming language to aid
with writing, compiling and running fault-tolerant quantum programs. As a toolkit, it provides:

- a framework to define QEC architectures;
- transformations through quantum program abstraction layers, from computational to logical to physical;
- verification tools to validate QEC primitive implementations.

Together, these enable automatic encoding of arbitrary Guppy programs, including measurement-dependent control flow.

```{code-cell} ipython3
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

For more examples, see these [notebooks](https://docs.quantinuum.com/guppy/ft/examples_index.html).

## Installation

As a Python package, `guppyft` can be installed from [PyPI](https://pypi.org/project/guppyft/) using `pip` or `uv`.

```{eval-rst}
.. tabs::

   .. code-tab:: shell pip

      pip install guppyft

   .. code-tab:: shell uv

      uv add guppyft
