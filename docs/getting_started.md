# Getting started

Guppy FT is an extension of the [Guppy](https://docs.quantinuum.com/guppy/) quantum programming language to enable fault-tolerant quantum programs.

In Guppy FT, we refer to a QEC architecture as the combination of a QEC code
definition, its collection of logical gadgets and their implementations, the
program transformation passes that let users encode their programs automatically, and
any code-specific policies used to manage resources at runtime, for instance
automated QEC insertion and state factories.

The purpose of Guppy FT is to provide tools for two kinds
of users:
* QEC-agnostic users that wish to use QEC in their experiments, treating QEC
as a black-box pass they can apply to their program. See the notebook example:
{doc}`examples/steane_encoding`.
* Advanced users that wish to co-design their experiments with particular QEC architectures,
having more control over how their program is encoded. See the notebook example:
{doc}`/examples/logical_program`.

Additionally, we encourage developers to define their own QEC architectures
following the Guppy FT framework, as described in the
[QEC architecture developer guide](architecture_dev.md).

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
