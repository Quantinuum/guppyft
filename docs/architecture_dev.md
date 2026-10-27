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

QEC architecture development in Guppy FT can be broken down into three milestones,
listed in the table below. These milestones successively support more features and,
crucially, enable a wider audience to use the architecture.

| Milestone                        | Target use case                        | Development task                                                                                     |
|----------------------------------|----------------------------------------|------------------------------------------------------------------------------------------------------|
| Implementation of QEC primitives | QEC prototyping and benchmarking       | Implement the QEC gadgets in Guppy                                                                   |
| Logical API                      | Application and QEC co-design          | Formalize the architecture's gate set, and define their implementations in terms of primitives       |
| End-to-end encoding              | "Push-button" encoding of applications | Specify how to compile arbitrary programs and automatically express them in terms of the logical API |

QEC developers are encouraged to target the milestone that best fits
the purpose and maturity of their architecture.
This page provides a high-level summary of the steps to complete each
milestone. We illustrate these with an example of a complete architecture for
the Steane $[[7,1,3]]$ code.
Note that more complex QEC architectures may require further
innovation from developers. In such cases, we will be keen to hear your
feedback, as we continue to evolve the framework to support a wider
variety of architectures.

The guidelines laid out on this page are meant to promote the adoption of a
common framework. Adhering to these guidelines will facilitate communication
and adoption of new features.


## Implementation of QEC primitives

We define a **primitive** as a function (usually written in Guppy) that implements a fundamental building
block of the QEC architecture. As a rule of thumb, these are physical circuits such as
state preparation, syndrome extraction, or transversal gates. We define these in a
{py:mod}`~guppyft.code.steane.primitives` module. The physical circuits may be written
directly using Guppy's {py:mod}`guppylang.std.quantum` library, or you may use
{py:mod}`guppylang.std.qsystem` to make explicit use of the Quantinuum device gate set.

### Verify logical semantics

Typically, it is not straightforward to check that the primitive implementation at
the physical level matches the intended logical action. We strongly recommend using
{py:mod}`guppyft.verify` to validate the logical action of Clifford primitives while
developing your architecture.

Using the verifier requires three definitions:

1. `semantic_function` is a Guppy function that defines the logical action on an
   array of $k$ logical qubits.
2. `impl_function` is a Guppy function that defines the physical implementation on
   an array of $n$ physical qubits or instances of `LogicalBlock[n]`.
3. `code_definition` is the {py:class}`~guppyft.code_def.StabilizerCode` definition, refer to the class docs for information on how to provide one for your code.

These definitions can then be used to as an assertion in the architecture test suite
using {py:func}`~guppyft.verify.valid_clifford_implementation`:

```python
from guppyft.verify import valid_clifford_implementation

semantic_function = ...  # logical action
impl_function = ...  # physical implementation
code_definition = ...  # stabilizer code reference

assert valid_clifford_implementation(semantic_function, impl_function, code_definition)
```

Equivalently, {py:func}`~guppyft.verify.valid_stabilizer_state_preparation` can be
used to check state preparation.

See the {doc}`/examples/clifford_verification` tutorial for
complete examples, including transversal and two-block gates, incorrect
implementations, and logical state preparation.

### Guidelines

Primitives are the most fundamental building blocks of the architecture. For instance,
magic-state preparation and injection are two separate primitives, but an
injection-based $T$ gate is not a primitive, as it comprises a preparation and an
injection. The aim is to give expert users maximum control over how to compose
primitives together, and easily replace them with alternative implementations.
Compositions of primitives into logical gadgets, such as a $T$ gate, belong to
the [logical API](#logical-api) as convenience functions.

For primitives that require measurements, be mindful of where
{py:meth}`~guppylang.std.quantum.Measurement.read` is called. This statement causes
the program to block until the outcome is available, and this can be an obstacle for
parallelization. When writing primitives, ensure you defer calling
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
* Developing compilation and optimization passes that transform logical programs;
* Supporting global management of resources, such as state factories;
* Writing programs at the logical level, which can then take advantage of the above
  features.

The steps for defining a logical API are the following:

### 1. Write logical HUGR extensions
Define logical operations and types to build HUGRs. This enables creating logical HUGRs,
as well as implementing compilation and optimisation passes that transform them.
For the Steane code, the logical operations and types are split into two extensions
`guppyft.steane.ops` and `guppyft.steane.types`. We recommend keeping to this pattern
to allow downstream users to rely on (usually slower changing) types without relying on
(usually faster changing, separately versioned) ops, although that is not mandatory.

At its core, a HUGR extension is a serialized JSON payload defining opaque types and how
opaque operations use those types. While you can manually define this payload, we recommend
using Rust to define the extensions and subsequently export them to JSON.
During development of the architectures native to Guppy FT, we use the `gen-extensions` command
from our [`justfile`](https://github.com/Quantinuum/guppyft/blob/main/justfile), which invokes
a Rust CLI (in [`cli.rs`](https://github.com/Quantinuum/guppyft/blob/main/extensions/src/cli.rs))
to dump the JSON of all known extensions.

Follow the Steane examples
for [`ops.rs`](https://github.com/Quantinuum/guppyft/blob/main/extensions/src/steane/ops.rs)
and [`types.rs`](https://github.com/Quantinuum/guppyft/blob/main/extensions/src/steane/types.rs)
to define the extensions, and export them to JSON using a similar mechanism to the above.
You should obtain payloads similar to
[`ops.json`](https://github.com/Quantinuum/guppyft/blob/main/src/guppyft//extensions/data/guppyft/steane/ops.json)
and [`types.json`](https://github.com/Quantinuum/guppyft/blob/main/src/guppyft//extensions/data/guppyft/steane/types.json).

Since you will be developing the architecture in Python, we additionally recommend to create
a Python API for your extension. Follow the pattern outlined in {py:mod}`guppyft.extensions.steane`.

### 2. Write logical Guppy operations

To enable downstream users to write logical programs using Guppy, you will need to provide
Guppy bindings for each HUGR op. These are special Guppy functions that, when compiled,
lower directly to HUGR op instantiations. Note that you can provide additional composite
logical actions by writing Guppy functions that in turn use the bindings. At the same time,
you can prevent exposure of some HUGR ops by marking their Guppy bindings as private and
discouraging direct use of them.

Follow the pattern of {py:mod}`guppyft.code.steane.logical`. Take care when defining composite actions:
You should not include any `guppylang.std.quantum` operations, as they will act on different types and
a different layer. An example of a composite operation in the Steane architecture is
{py:func}`guppyft.code.steane.logical.t`, which is performed through magic-state injection.

### 3. Define op implementations

Up to this point, the logical operations are not yet executable, since they are HUGR ops that are unknown to
the target machine or emulator. A single logical operation may have many different possible implementations to choose
from. Replacing an operation with its implementation is essentially a HUGR to HUGR transform, so we can write it as such
a transformation pass.

The Steane architecture (see {py:mod}`guppyft.code.steane.encode`) defines this pass using the
{py:func}`guppyft.encode.implement_ops` utility and the related {py:class}`guppyft.encode.ImplementOpsSpec`,
by providing 1. an implementation for every opaque operation and 2. the runtime state needed for these
implementations (see [the runtime state section](#tracking-runtime-state) for more information),
including state setup and teardown. After transformation of a HUGR package the result is an executable
HUGR with an entrypoint.

### 4. (Optional) Additional transformation passes

Optionally, you may want to define different QEC-aware optimization passes that run on the
logical HUGR. For example, this could include optimizing qubit allocation into blocks for
$k>1$ codes using dataflow analysis.

The Steane architecture currently defines no such passes.

### Logical API versus primitives

Adding a logical API step is necessary to provide an abstraction layer on top of
{py:mod}`~guppyft.code.steane.primitives`, where we can define compilation and
optimization passes and global management of resources. It provides a useful
separation of concerns: we may build and transform logical HUGRs without involving
the low-level physical details, then link their physical implementation as a
final `implement_ops` pass. This abstraction lets developers provide a public
interface for the logical operations, while keeping the details of the physical
circuits private.

### Tracking runtime state

A key enabler for Guppy FT is the ability to track and manage logical resources and
operations at runtime. You can achieve this by e.g. defining a Guppy struct that tracks
global state, making it available to logical operations. In the
Steane architecture, {py:class}`~guppyft.code.steane.encode.SteaneBuilder` defines
the `STATE` struct to track and manage logical resources at runtime, which includes:

- Allocation and freeing of logical blocks;
- Parallel zero and magic state preparation through state factories;
- Runtime QEC cycle insertion.

`STATE` tracks available logical-qubit addresses in a stack. Allocating a qubit pops
an address from the stack, while freeing it returns the address to the stack.
Addresses are `(block_id, qubit_id)` tuples. As Steane is a $k=1$ code, `qubit_id` is fixed;
however, representing addresses as tuples allows the same approach to support codes with
multiple logical qubits per block. In those cases, addressable multi-qubit logical operations
may have to decide at runtime which primitives to use (e.g. intra-block vs inter-block).

To make the state available to logical operations, the Steane architecture currently uses
global LLVM variables, following a pattern of:
1. Set up and initialize the state
2. Run the user provided entrypoint in a global-enabled context using {py:func}`~guppyft.globals.with_global`
    - Implementations will have access to the state using {py:func}`~guppyft.globals.map_global`.
3. Tear down the state

You can find examples of global usage and this pattern in {py:class}`~guppyft.code.steane.encode.SteaneBuilder`.

```{warning}
Be mindful that complex classical computation at runtime can hinder
performance on the quantum device if it causes stalling.
```

### Guidelines

As a rule of thumb, the operations exposed in the HUGR extension should
match the Guppy functions in {py:mod}`~guppyft.code.steane.primitives` with the same
name. Functions that are not to be exposed should be marked as private in
{py:mod}`~guppyft.code.steane.primitives` by beginning their name with an underscore.

You may provide composite functions in {py:mod}`~guppyft.code.steane.logical`,
such as the $T$ gate implemented in {py:func}`guppyft.code.steane.logical.t`.
These composite functions should not have corresponding HUGR operations; the
HUGR extension should only include the fundamental primitives of the architecture.

Defining the op implementation pass efficiently may be tricky, and `implement_ops` provides
several opportunities for improving pass performance like grouping the actual op implementations
into a single Guppy library that is linked in later, avoiding duplicate compilation
of e.g. the global state. The Steane architecture leverages most of these opportunities.

We recommend using the [semver](https://semver.org/) convention for the versioning of
the HUGR extension(s).

## End-to-end encoding

Thus far, we have defined a [logical API](#logical-api), defined the
[primitives](#implementation-of-qec-primitives) to implement them, and
how the individual logical operations are [mapped to these primitives](#3-define-op-implementations).
This is sufficient for users to write programs using the logical API and running
them on the target. However, some users may want to write at the QEC code agnostic
computational layer, so we need to provide a lowering for them to the logical API of our code.

Define a `compile` pass that transforms the computational HUGR into a logical
HUGR using the operations from the [logical API](#logical-api). In the Steane architecture, we
use the {py:class}`guppyft.encode.ReplacementCompiler` to replace
supported `guppylang.std.quantum` operations with a corresponding operation
from the {py:mod}`guppyft.code.steane.logical` API. More complex architectures,
most notably those for `k>1` codes, will require a bespoke compiler to be developed, for
example when the architecture wants to make use of statically allocating logical qubits
into code blocks (to leverage more efficient operations).

Ideally, any logical compiler would support all quantum operations provided
by {py:mod}`guppylang.std.quantum`. Naturally, you may choose to support only a
subset of these. The encoding pass will fail on user programs outside this subset.
Using an architecture with operations outside of its supported set requires decompositions,
such as the one we support for computational `Rz` gates with runtime angles, following
["Single-qubit rotation algorithm with logarithmic Toffoli count and gate depth"](https://arxiv.org/pdf/2404.05618).
These decompositions are naturally not architecture specific and may be reused.

### Guidelines

Most architectures will have some options for configurability, for example to tune the runtime
policies that manage state factories and QEC cycle insertion. To enable this, we recommend an immutable
builder pattern over a single factory function with many parameters, both for flexibility
and maintenance.

Following our Steane example, our architecture is defined in
{py:mod}`guppyft.code.steane.encode` which defines the
{py:class}`~guppyft.code.steane.encode.SteaneBuilder`
class for users to build a specific architecture instance based on provided
parameters. Usage of this class is illustrated in the end-to-end encoding notebook
{doc}`/examples/steane_encoding`.


## Further resources

* Guppy language [documentation](https://docs.quantinuum.com/guppy/).
* HUGR [repository](https://github.com/Quantinuum/hugr): defines the IR of the
  Quantinuum software stack.
* TKET [repository](https://github.com/Quantinuum/tket2): implements compilation
  and optimisation passes that act on HUGRs.
