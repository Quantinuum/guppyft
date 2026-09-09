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
:maxdepth: 1
:hidden:

examples_index.md
api/api.md
```

Guppy FT is an extension of the [Guppy](https://docs.quantinuum.com/guppy/) quantum programming language to enable fault-tolerant quantum programs.

In Guppy FT, we refer to a QEC architecture as the combination of a QEC code
definition, its collection of logical gadgets and their implementations, the
program transformation passes that let users encode their programs automatically, and
any code-specific policies used to manage resources at runtime, for instance
automated QEC insertion and state factories.

The purpose of Guppy FT is to provide tools for two kinds
of users:
* QEC-agnostic users that wish to use QEC in their experiments, treating QEC
as a black-box pass they can apply to their program. (**TODO** link to end-to-end notebook).
* Advanced users that wish to co-design their experiments with particular QEC architectures,
having more control over how their program is encoded. ({doc}`/examples/logical_program`).

Additionally, we encourage developers to define their own QEC architectures
following the Guppy FT framework, as described in (**TODO** link to QEC architecture dev guide).

For the sake of separation of concerns, we find it useful to think about programs
at three different levels of abstraction:
* **Computational** - The program assumes a noiseless device and arbitrary gate set. This is the kind of program that the QEC-agnostic users write, using Guppy.
* **Logical** - The program uses the gate set of the QEC architecture, using a logical Guppy library provided by the QEC architecture.
The user may want to specify where to introduce QEC cycles and how to handle state preparation explicitly, or defer to automated methods.
* **Physical** - The program with all of its logical gadgets implemented as physical circuits. These programs are ready for submission to a quantum device.

Guppy FT provides transformations to lower the user program through these levels of
abstraction. We use the following naming convention:
* `compile` refers to the transformation of a computational program into a logical program. It involves transforming the program to use the logical gate set, as well as introducing QEC cycles and resource-state preparation.
* `implement_ops` refers to the transformation of a logical program into a physical program. It involves linking the opaque logical gadget declarations to their physical implementation.
* `encode` refers to the composition of the above, transforming a computational program all the way to physical.


## Installation

As a Python package, `guppyft` can be installed from [PyPI](https://pypi.org/project/guppyft/) using `pip` or `uv`.

```{eval-rst}
.. tabs::

   .. code-tab:: shell pip

      pip install guppyft

   .. code-tab:: shell uv

      uv add guppyft
```

The source for `guppyft` is available on [GitHub](https://github.com/quantinuum/guppyft/). If you have a feature request or think you have found a bug, feel free to raise a [GitHub issue](https://github.com/quantinuum/guppyft/issues).


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

The resulting package is runnable and fully compatible with Selene, locally or through Nexus cloud, and can
be submitted to quantum devices. `SteaneInstance` includes an `emulator` helper method to aid with emulating the resulting encoded program locally. Below, we demonstrate simulating our encoded program using Stim:

```{code-cell} ipython3
from selene_sim import Stim

steane.emulator(teleportation.compile(), n_qubits=22).with_simulator(Stim()).run().collated_shots()
```
