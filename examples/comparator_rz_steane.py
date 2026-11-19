import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Comparator-based Rz synthesis with the Steane architecture

    > ⚠️ **Warning**
    >
    > Comparator-based synthesis combined with Steane encoding requires a large number of physical gates, even for simple programs. Running programs produced by this workflow on current hardware will likely exceed practical runtime limits and may result in timeout errors.

    The Steane architecture supports Clifford+$T$ operations, but not arbitrary $Rz$ rotations. This notebook demonstrates using [`ComparatorRzDecomposer`](https://docs.quantinuum.com/guppy/ft/api/generated/guppyft.decompose.ComparatorRzDecomposer.html#guppyft.decompose.ComparatorRzDecomposer) to approximate $Rz$ gates with a comparator-based decomposition, then encodes the resulting Clifford+$T$ program using the Steane architecture. The method uses a repeat-until-success subroutine that can be used on arbitrary angles $\theta$ at runtime and is based on the paper ["Single-qubit rotation algorithm with logarithmic Toffoli count and gate depth"](https://arxiv.org/pdf/2404.05618).

    The comparator decomposition uses $2\lceil\log_2(1 / \varepsilon)\rceil$ ancilla qubits and introduces Toffoli gates. Its probability of success on each $Rz$ decomposition attempt is greater than $1/2$; a shot is discarded if any of the $Rz$ gates in the program fail to be decomposed after the specified number of attempts (`max_attempts`).

    To learn more about the comparator decomposition, see the [Comparator-based Rz synthesis](https://docs.quantinuum.com/guppy/algorithms/examples/rotation_synthesis/comparator_based_rz.html) example in `guppyalgos`.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Define a program with a runtime rotation

    The angle is generated at runtime to demonstrate that `ComparatorRzDecomposer` can decompose both static and runtime angles. Applying the angle and its inverse returns the target to $\ket{+}$; a final Hadamard and computational-basis measurement should therefore return `0`.
    """)
    return


@app.cell
def _():
    from guppylang import guppy
    from guppylang.std.platform import output
    from guppylang.std.qsystem.random import RNG
    from guppylang.std.quantum import h, measure, qubit, rz

    @guppy
    def random_rz() -> None:
        rng = RNG(123)
        theta = rng.random_angle()
        rng.discard()

        target = qubit()
        h(target)
        rz(target, theta)
        rz(target, -theta)
        h(target)
        output("result", measure(target).read())

    return (random_rz,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Decompose before encoding

    `ComparatorRzDecomposer` replaces every `Rz` with its comparator-based decomposition, which adds Toffoli gates. [`ToffoliDecomposer`](https://docs.quantinuum.com/guppy/ft/api/generated/guppyft.decompose.ToffoliDecomposer.html#guppyft.decompose.ToffoliDecomposer) must therefore run next, converting each Toffoli to Clifford+$T$. The resulting package can then be encoded by the Steane architecture.
    """)
    return


@app.cell
def _(random_rz):
    from guppyft.decompose import ComparatorRzDecomposer, ToffoliDecomposer

    # Compile the package with minimal optimization
    # to avoid `rz` angles being squashed
    pkg = random_rz.with_minimal_opt().compile()
    rz_decomposer = ComparatorRzDecomposer(epsilon=0.1, max_attempts=15)
    rz_decomposer.then(ToffoliDecomposer()).run(pkg.modules[0], inplace=True)

    print(f"Comparator ancillas: {rz_decomposer.n_ancillas()}")
    return pkg, rz_decomposer


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Encode and emulate with the Steane architecture

    The comparator ancillas need to be encoded as well, so the Steane architecture needs one logical block for each of them. It also needs one block for the target qubit and one workspace block for magic-state injection. Each Steane block occupies seven physical qubits; the additional three physical qubits are used as flag ancillas during state preparation.

    The `Coinflip` simulator is sufficient to exercise the compilation and control flow, but does not simulate the quantum state. We set the `bias=0.0` in the simulator to force all measurements to be 0 to select the success branch during the comparator synthesis and, in the case of the encoded program, to ensure all RUS state preparations succeed. We attach a `CircuitExtractor` to the emulator to compare the two-qubit depth before and after Steane encoding.

    Even at the relaxed precision used here, the forward-and-inverse pair expands to a large number of physical two-qubit gates. This makes comparator-based synthesis combined with Steane encoding prohibitive on current hardware: the circuit is likely to exceed practical runtime limits, and accumulated two-qubit gate error would dominate the result. Use this workflow to study fault-tolerant resource costs rather than as a near-term hardware implementation.
    """)
    return


@app.cell
def _(pkg, rz_decomposer):
    from guppylang.emulator import EmulatorBuilder
    from selene_sim.backends.bundled_simulators import Coinflip
    from selene_sim.event_hooks.instruction_log import CircuitExtractor

    from guppyft.code.steane.encode import SteaneBuilder

    logger = CircuitExtractor()
    (
        EmulatorBuilder()
        .build(pkg, n_qubits=1 + rz_decomposer.n_ancillas())
        .with_simulator(Coinflip(bias=0.0))  # Set bias=0.0 to select success branches
        .with_event_hook(logger)
    ).run()
    unencoded_two_qubit_depth = logger.shots[0].get_user_circuit().depth_2q()

    steane = SteaneBuilder().build(n_blocks=10)
    _results = (
        steane.emulator(pkg, n_qubits=73)
        .with_simulator(Coinflip(bias=0.0))  # Set bias=0.0 to select success branches
        .with_event_hook(logger)
        .run()
    )
    encoded_two_qubit_depth = logger.shots[1].get_user_circuit().depth_2q()

    print("Two-qubit depth:")
    print(f"\tBefore Steane encoding: {unencoded_two_qubit_depth}")
    print(f"\tAfter Steane encoding: {encoded_two_qubit_depth}")
    return


if __name__ == "__main__":
    app.run()
