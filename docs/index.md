---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
kernelspec:
  name: python3
  display_name: Python 3
---

# Getting started

```{toctree}
:hidden:
:maxdepth: 1

api/api.md
```

Guppy FT is an extension of the [guppylang](https://github.com/Quantinuum/guppylang) quantum programming language to enable fault-tolerant quantum programs.

## Installation

As a Python package, [Guppy FT](https://pypi.org/project/guppyft/) can be installed from PyPI using `pip` or `uv`.

```{eval-rst}
.. tabs::

   .. code-tab:: shell pip

      pip install guppyft

   .. code-tab:: shell uv

      uv add guppyft
```

The source for Guppy FT is available on [GitHub](https://github.com/quantinuum/guppyft/). If you have a feature request or think you have found a bug, feel free to raise a [GitHub issue](https://github.com/quantinuum/guppyft/issues).

## Naming convention

In Guppy FT, we refer to a QEC architecture as the combination of a QEC code
definition, its collection of logical gadgets and their implementation, the
compilation passes that let users encode their programs automatically, and
any code-specific policies used to manage resources at runtime, for instance
automated QEC insertion and state factories.

Furthermore, the goal of Guppy FT is to provide tools for two kinds
of users


## Example: Encoding with Steane

Let's demonstrate automatic encoding using Guppy FT. We begin by writing our quantum program in Guppy. At this stage, we are writing a _computational_ program that is QEC-agnostic. For this example, we use the quantum teleportation primitive.

```{code-cell} ipython3
from guppylang import guppy
from guppylang.std.builtins import output
from guppylang.std.quantum import cx, h, measure, qubit, x, z

@guppy
def teleportation() -> None:
    # Init source qubit in the |1> state
    src = qubit()
    x(src)

    # Create Bell pair
    tmp = qubit()
    tgt = qubit()
    h(tmp)
    cx(tmp, tgt)

    # Teleport
    cx(src, tmp)
    h(src)
    if measure(src).read():
        z(tgt)
    if measure(tmp).read():
        x(tgt)

    output("tgt", measure(tgt).read())
```

Notice that our teleportation program is written using only `guppylang` operations, and does not require any knowledge of QEC. The intention at this stage is to ensure that the algorithm is correct, without taking noise into consideration.

We can now select the QEC code architecture that we would like to use to encode our program. In this example, we will use the Steane architecture available in {py:mod}`guppyft.code.steane`. We can define an instance of the architecture using {py:class}`guppyft.code.steane.encoder_spec.SteaneBuilder` by providing the number of logical blocks, `n_blocks`, available during execution. In our case, we need 3 blocks for our teleportation program.

```{code-cell} ipython3
from guppyft.code.steane.encode import SteaneBuilder

steane = SteaneBuilder().build(n_blocks=3)
```

With our Steane architecture instance, we can encode our program using {py:func}`guppyft.code.steane.encoder_spec.SteaneInstance.encode` to produce a HUGR package composed of lowered, logical primitives.
```{code-cell} ipython3
pkg = steane.encode(teleportation.compile())
```

The resulting package is runnable and fully compatible with `Selene`, locally or through `Nexus`, and running on production hardware. `SteaneInstance` includes an `emulator` helper method to aid with emulating the resulting encoded program locally. Below, we demonstrate simulating our encoded program using `Stim`:

```{code-cell} ipython3
from selene_sim import Stim

steane.emulator(teleportation.compile(), n_qubits=100).with_simulator(Stim()).run().collated_shots()
```
