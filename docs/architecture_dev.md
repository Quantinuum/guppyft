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

This guide describes how QEC developers can build their own architectures using the
Guppy FT framework. A QEC architecture is more than a library of logical gadgets: it
includes the policies to manage resources at runtime (e.g. state factories) and the
interfaces and compilation passes that enable others to use them with ease. On this
page, we refer to the **computational**, **logical** and **physical**
abstraction layers defined in the [Getting Started](index.md) page.

QEC architecture development in Guppy FT can be broken down into the three milestones,
listed in the table below. Each milestone supports more features and, crucially, enables
a wider audience to use the architecture.

| Milestone                        | Target use case                        | Development task                                                                  |
|----------------------------------|----------------------------------------|-----------------------------------------------------------------------------------|
| Implementation of QEC primitives | QEC prototyping & benchmarking         | Implement the QEC gadgets in Guppy                                                |
| Logical API                      | Application & QEC co-design            | Formalize the architecture's gate set                                             |
| End-to-end encoding              | "Push-button" encoding of applications | Specify how to compile arbitrary programs, and how to manage resources at runtime |

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

We define a **primitive** as a Guppy function that implements a fundamental building
block of the QEC architecture. As a rule of thumb, these are physical circuits such as
state preparation, syndrome extraction, or transversal gates. We define these in a
{py:mod}`~guppyft.code.steane.primitives` module. The physical circuits may be written
directly using Guppy's {py:mod}`guppylang.std.quantum` library, or you may use
{py:mod}`guppylang.std.qsystem` to make explicit use of the Quantinuum device gate set.

### Guidelines

Primitives are the most fundamental building blocks of the architecture. For instance,
magic-state preparation and injection are two separate primitives, but an
injection-based $T$ gate is not a primitive as it comprises a preparation and an
injection. This is to provide expert users maximum control over how to compose
primitives together, and easily replace them with alternative implementations.
Compositions of primitives into logical gadgets, such as a $T$ gate, belong to
the [logical API](#logical-api) as convenience functions.

Where primitives require measurements, be mindful of where
{py:meth}`~guppylang.std.quantum.Measurement.read` is called. This statement causes
the program to wait until the outcome is available, which can be an obstacle for
parallelization. When writing primitives ensure you defer calling
{py:meth}`~guppylang.std.quantum.Measurement.read` on measurements as late as possible.

To see an example of how to defer measurements to maximize parallelism, see the
fault-tolerant $T\ket{+}$ state preparation in the Steane architecture
{py:mod}`~guppyft.code.steane.primitives`. We wrap the logical block in a Guppy
{py:class}`~guppyft.std.state_factory.PreBlock` struct that contains an array
of {py:class}`~guppylang.std.quantum.Measurement` and a
{py:meth}`~guppyft.std.state_factory.PreBlock.force_check` method which calls
{py:meth}`~guppylang.std.quantum.Measurement.read` on all measurements. This enables
parallelization of state preparation via
{py:class}`~guppyft.std.state_factory.StateFactory`.

## Logical API

Providing a logical API to the QEC architecture enables describing, creating and
transforming HUGRs at the logical abstraction layer. This includes:
* Developing compilation and optimization passes that transform logical programs.
* Supporting global management of resources, such as state factories.
* Writing programs at the logical level, which can then take advantage of the above
  features.

The steps for defining a logical API are the following:

1. **Logical HUGR extensions** - Define logical operations and types to build HUGRs.
   This enables creating logical HUGRs, as well as implementing compilation
   and optimisation passes that transform logical HUGRs.
   * Two HUGR extensions are generated using Rust for the operations and types
     required by the architecture.
   * Follow the Steane examples
     for [`ops.rs`](https://github.com/quantinuum-dev/guppyft/blob/main/extensions/src/steane/ops.rs)
     and [`types.rs`](https://github.com/quantinuum-dev/guppyft/blob/main/extensions/src/steane/types.rs).
   * The extensions are separated so that they can be versioned separately.
   * Run `just gen-extensions` to automatically generate the JSON files of the HUGR
     extension.
2. **Logical Guppy bindings** - Provide the Guppy interface to create programs
   directly at the logical level.
   * Follow the pattern in {py:mod}`guppyft.code.steane.logical`.
   * The logical operations of the code include bindings for the operations and
     types in the HUGR extensions.
   * Additionally, developers may define composite logical operations.
     These composite operations should be written in terms
     of other logical operations, and should not include any `guppylang.std.quantum`
     operations An example of a composite operation in the Steane architecture is
     {py:func}`guppyft.code.steane.logical.t` that is performed through magic-state
     injection.
3. **Define resource structures** - Provide structures to manage logical resources
   at runtime, such as resource state generation. These resources will be
   architecture dependent and are optional.
   * The Steane architecture uses state factories to parallelize preparation of
     $\ket{0}$ and $T\ket{+}$ states.
   * A {py:class}`~guppyft.std.state_factory.PreBlock` Guppy struct wraps the
     logical block together with the flag measurements.
   * The {py:class}`~guppyft.std.state_factory.StateFactory` then manages
     parallel preparation of `PreBlock`s.
   * Similar resources could be defined to manage logical measurements or QEC cycles.
4. **Transformation passes** - Define transformation passes between the
   computational, logical and physical abstraction layers. Depending on the chosen
   target milestone, these may be optional.
   * Define a `compile` pass that transforms the computational HUGR into a logical
     HUGR using the operations defined in step 1. In the Steane architecture, we
     use the {py:class}`guppyft.encode.ReplacementCompiler` to replace
     supported `guppylang.std.quantum` operations with a corresponding operation
     from the {py:mod}`guppyft.code.steane.logical` API. More complex architecture will
     require a new HUGR compiler to be developed.
   * Define the `implement_ops` pass to link opaque logical API operations to their
     [physical implementation](#implementation-of-qec-primitives). The
     Steane architecture uses the default `implement_ops` pass. See
     the [end-to-end](#end-to-end-encoding) section for more detail.
   * Optionally, we can define QEC-aware optimization passes on the logical HUGR.
     For example, this could include optimizing qubit allocation into blocks for
     $k>1$ codes.

### What distinguishes the Logical API from primitives?

Adding a logical API step is necessary to provide an abstraction layer on top of
{py:mod}`~guppyft.code.steane.primitives`, where we can define compilation and
optimisation passes and global management of resources. It provides a useful
separation of concerns: we may build and transform logical HUGRs without involving
the low-level physical details, then link their physical implementation as a
final `implement_ops` pass. This abstraction lets developers provide a public
interface for the logical operations, while keeping the details of the physical
circuits private.

### Guidelines

As a rule of thumb, the operations exposed in the HUGR extension should
match the Guppy functions in {py:mod}`~guppyft.code.steane.primitives` with the same
name. Functions that are not to be exposed should be marked as private in
{py:mod}`~guppyft.code.steane.primitives` by beginning their name with an underscore.

You may provide composite functions in {py:mod}`~guppyft.code.steane.logical`,
such as the $T$ gate implemented in {py:func}`guppyft.code.steane.logical.t`.
These composite functions should not have corresponding HUGR operations; the
HUGR extension should only include the fundamental primitives of the architecture.

Ideally, any logical compiler would support all quantum operations provided
by {py:mod}`guppylang.std.quantum`. Naturally, you may choose to support only a
subset of these. The encoding pass will fail on user programs outside this subset.
We intend to provide default decompositions for some of these gates in future releases.

We recommend using the [semver](https://semver.org/) convention for the versioning of
the HUGR extension.

## End-to-end encoding

We are now able to combine the
[primitives](#implementation-of-qec-primitives) and [logical API](#logical-api)
building blocks into a single architecture builder to enable users to automatically encode
their Guppy programs. This is illustrated in the end-to-end encoding notebook
{doc}`/examples/steane_encoding`.

Following our Steane example, our architecture is defined in
{py:mod}`guppyft.code.steane.encode` which defines the
{py:class}`~guppyft.code.steane.encode.SteaneBuilder`
class for users to build a specific architecture instance based on provided
parameters.

A key enabler for Guppy FT is the ability to track and manage logical resources and
operations at runtime. This is achieved by defining a Guppy struct, and performing
logical operations in a global-context where the global state is available. In the
Steane architecture, {py:class}`~guppyft.code.steane.encode.SteaneBuilder` defines
the `STATE` struct to track and manage logical resources at runtime, which includes:

- Allocation and freeing of logical blocks.
- Parallel zero and magic state preparation through state factories.
- Runtime QEC cycle insertion.

`STATE` tracks available logical-qubit addresses in a stack. Allocating a qubit pops
an address from the stack, while freeing it returns the address to the stack.
Addresses are `(block_id, qubit_id)` tuples. However, as Steane is a
$k=1$ code, `qubit_id` is always fixed; representing addresses as tuples allows the
same approach to support codes with multiple logical qubits per block.

The architecture wrapper creates the initial `STATE` and calls
{py:func}`~guppyft.globals.with_global` to run the encoded program in a
global-enabled context. Replacement operation implementations then use
{py:func}`~guppyft.globals.map_global` to access the state: it passes the current
state as the first argument to the replacement implementation, which returns the
updated state followed by any ordinary return values. Examples of primitives being
run in the global context can be found in
{py:class}`~guppyft.code.steane.encode.SteaneBuilder`.


### Guidelines

Since Guppy supports classical logic at runtime, you may provide adaptive decompositions
of gates. For instance, our reference Steane architecture supports `Rz` gates
with angles determined at runtime, following the approach
from ["Single-qubit rotation algorithm with
logarithmic Toffoli count and gate depth"](https://arxiv.org/pdf/2404.05618).
Architectures where each code block contains multiple logical qubits can
support arbitrary gate addressing by tracking the qubit assignment at runtime (as
in the global `STATE` from {py:mod}`~guppyft.code.steane.encode`) and using `if`
statements to resolve how to decompose the computational gates into logical
operations.
Be mindful that complex classical computation at runtime can lead to adverse
performance on the quantum device if it causes stalling.


## Further resources

* Guppy language [documentation](https://docs.quantinuum.com/guppy/).
* HUGR [repository](https://github.com/Quantinuum/hugr): defines the IR of the
  Quantinuum software stack.
* TKET [repository](https://github.com/Quantinuum/tket2): implements compilation
  and optimisation passes that act on HUGRs.
