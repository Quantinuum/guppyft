---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
kernelspec:
  name: python3
  display_name: Python 3
---

# QEC architecture developer guide

This guide describes how QEC developers can build their own architectures using
the Guppy FT framework.
A QEC architecture is more than a library of logical gadgets: it includes the
policies to manage resources at runtime (e.g. state factories) and the
interfaces and compilation passes that enable others to use them with ease.
On this page, we refer to the *computational*, *logical* and *physical* abstraction
layers defined in the starter page (**TODO**: link).

QEC architecture development in Guppy FT can be broken down into the three milestones,
listed in the table below.
Each milestone supports more features and, crucially, enables a wider audience
to use the architecture.

| Milestone | Target use case | Development task |
|---|---|---|
| Implementation of QEC primitives | QEC prototyping & benchmarking | Implement the QEC gadgets in Guppy |
| Logical API | Application & QEC co-design | Formalize the architecture's gate set |
| End-to-end encoding | "Push-button" encoding of applications | Specify how to compile arbitrary programs, and how to manage resources at runtime |

QEC developers are encouraged to target the milestone that best fits
the purpose and maturity of their architecture.
This page provides a high-level summary of the steps to complete each
milestone. We illustrate these with an example of a complete architecture for
the Steane $[[7,1,3]]$ code, with links to the relevant source code in our repository.
Note that more complex QEC architectures may require further
innovation from developers. In such cases, we will be keen to hear your
feedback, as we continue to evolve the framework to support a wider
variety of architectures.

The guidelines laid out on this page are meant to promote the adoption of a
common framework. Adhering to these guidelines will facilitate communication
and adoption of new features.


## Implementation of QEC primitives

We define a *primitive* as a Guppy function that implements a fundamental building
block of the QEC architecture.
As a rule of thumb, these are physical circuits:
state preparation, syndrome extraction, transversal gates...
We define these in a [primitives.py](https://github.com/quantinuum-dev/guppyft/blob/main/src/guppyft/code/steane/primitives.py) file. The physical
circuits may be written directly using Guppy's `guppylang.std.quantum` library,
or you may use `guppylang.std.qsystem` to make explicit use of a Quantinuum device
gate set.

### Guidelines

Primitives are the most fundamental building blocks of the
architecture. For instance, magic state preparation and injection are two
separate primitives, but an injection-based $T$ gate is not a primitive on its
own.
This is so that expert users have maximum control over how to compose
primitives together, and easily replace them with alternative implementations.
Compositions of primitives into logical gadgets &mdash;such as a $T$ gate&mdash;
belong to the [logical API](#logical-api) as convenience functions.

When applying measurements, be mindful of where you call `read()`.
This statement causes the program to wait until the outcome is available, which
can be an obstacle for parallelization.
You should write primitives that defer measurement `read()` as
late as possible.
For instance, see our fault-tolerant $\lvert H \rangle$ state preparation in Steane's [`primitives.py`](https://github.com/quantinuum-dev/guppyft/blob/main/src/guppyft/code/steane/primitives.py):
we wrap a logical block in another Guppy struct, `PreBlock` (see [source code](https://github.com/quantinuum-dev/guppyft/blob/main/src/guppyft/code/_state_factory.py)),
that contains an array of `Measurement` objects and a `force_check()` method which
calls `read()` on all measurements.
This enables parallelization of state preparation via `StateFactory` (see [source code](https://github.com/quantinuum-dev/guppyft/blob/main/src/guppyft/code/_state_factory.py)).


## Logical API

Providing a logical API to the QEC architecture enables the following features.
* Developing compilation and optimization passes that transform logical programs.
* Supporting global management of resources, such as state factories.
* Writing programs at the logical level, which can then take advantage
of the above features.

The steps for defining a logical API are the following.
1. Define a HUGR extension for the code.
    * The HUGR extension is generated using Rust. Follow the Steane example
    for [`ops.rs`](https://github.com/quantinuum-dev/guppyft/blob/main/extensions/src/steane/ops.rs)
    and [`types.rs`](https://github.com/quantinuum-dev/guppyft/blob/main/extensions/src/steane/types.rs).
    * Run `just gen-extensions`. This will automatically generate the JSON files of the HUGR extension.
2. Define the logical library of the code, following the pattern in [`logical.py`](https://github.com/quantinuum-dev/guppyft/blob/main/src/guppyft/code/steane/logical.py).
3. Define an architecture instance, following the pattern of `SteaneInstance` from [`encode.py`](https://github.com/quantinuum-dev/guppyft/blob/main/src/guppyft/code/steane/encode.py).
4. Define an architecture builder, following the pattern of `SteaneBuilder` from [`encode.py`](https://github.com/quantinuum-dev/guppyft/blob/main/src/guppyft/code/steane/encode.py).
    * You do not need to provide a `logical_compiler` to `_gen_encoder_spec`; this is
      only a requirement for [end-to-end encoding](#end-to-end-encoding).
    * The key contribution is `_gen_implement_spec`. Using the `STATE` class is optional;
      it provides a global context for resource management.

Step 1 creates new operations and types to build logical HUGRs. It enables
the implementation of compilation and optimization passes that transform
logical HUGRs.
Step 2 provides a Guppy interface to create programs to be compiled to these new HUGR
operations and types, as illustrated in the "Writing Logical Programs" notebook
(**TODO**: provide link).
Steps 3 and 4 provide the `implement_ops` method showcased in the same
notebook; this replaces the opaque logical operations with their physical implementations
from [primitives.py](https://github.com/quantinuum-dev/guppyft/blob/main/src/guppyft/code/steane/primitives.py).
If `STATE` is implemented, it may be used to track global information on the program
at runtime, enabling the development of runtime policies such as dynamic logical
qubit allocation, automated QEC insertion and state factory management.

Currently, these steps involve writing some boilerplate source code.
We intend to streamline this process with automation in future releases.


### Can't I do this already with `primitives.py`?

This step is necessary to provide an abstraction layer on top of `primitives.py`
where we can define compilation and optimization passes and global management
of resources. It provides a useful separation of concerns: we may build and transform
logical HUGRs without involving the low-level physical details, then *link* their
physical implementation as a final pass &mdash;`implement_ops`.
This abstraction lets developers provide a public interface for the logical operations,
while keeping the details of the physical circuits private.


### Guidelines

As a rule of thumb, the operations exposed in the HUGR extension should
match the Guppy functions in `primitives.py` with the same name. Functions that
are not to be exposed should be marked as private in `primitives.py`
by beginning their name with an underscore.

You may provide convenience functions in [`logical.py`](https://github.com/quantinuum-dev/guppyft/blob/main/src/guppyft/code/steane/logical.py), such as the $T$ gate from the Steane architecture reference.
We suggest these convenience functions do not have corresponding HUGR operations; the
HUGR extension should only include the fundamental building blocks of the architecture.

We recommend using the [semver](https://semver.org/) convention for the versioning of
the HUGR extension.


## End-to-end encoding

This enables users to automatically encode their Guppy programs using the
QEC architecture you develop, as illustrated in the end-to-end encoding notebook (**TODO**: link).
To provide this functionality, you must implement a `logical_compiler` and pass it to
`_gen_encoder_spec` as demonstrated in [`encode.py`](https://github.com/quantinuum-dev/guppyft/blob/main/src/guppyft/code/steane/encode.py).
This handles the compilation of a computational Guppy program to a logical HUGR using
your architecture's logical API.

The [reference Steane architecture](https://github.com/quantinuum-dev/guppyft/blob/main/src/guppyft/code/steane/encode.py)
uses a `ReplacementCompiler` that can replace individual HUGR operations with a
specified logical HUGR operation &mdash;from your logical API&mdash; or (the compiled HUGR of) a Guppy
function you provide &mdash;useful for convenience functions, such as $T$.
If your architecture requires further flexibility, for instance, replacing
subcircuits with other subcircuits, you will need to develop your own HUGR
transformation pass.


### Guidelines

Ideally, your logical compiler would support all quantum operations provided
by [`guppylang.std.quantum`](https://docs.quantinuum.com/guppy/api/generated/guppylang.std.quantum.html#module-guppylang.std.quantum).
Naturally, you may choose to support only a subset of these. The encoding pass will fail on
user programs outside this subset.
We intend to provide default decompositions for some of these gates in future releases.

Since Guppy supports classical logic at runtime, you may provide adaptive decompositions
of gates. For instance, our reference Steane architecture supports `Rz` gates
with angles determined at runtime, following https://arxiv.org/pdf/2404.05618.
Architectures where each code block contains multiple logical qubits can
support arbitrary gate addressing by tracking the qubit assignment at runtime
&mdash;as in the global `STATE` from [`encode.py`](https://github.com/quantinuum-dev/guppyft/blob/main/src/guppyft/code/steane/encode.py)&mdash;
and using `if` statements to resolve how to decompose the computational gate into
logical operations. (**TODO** point to a k>1 example doing this).
*Caveat*: be mindful that complex classical computation at runtime can lead to adverse
performance on the quantum device if it causes stalling.


## Further resources

* Guppy language [documentation](https://docs.quantinuum.com/guppy/).
* HUGR [repository](https://github.com/Quantinuum/hugr): defines the
IR of Quantinuum's software stack.
* TKET [repository](https://github.com/Quantinuum/tket2): implements compilation
and optimization passes that act on HUGRs.
