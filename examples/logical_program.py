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
    # Writing logical programs directly

    Guppy FT supports advanced users who want to write programs using the logical operations of a QEC architecture directly, allowing them to manually optimize their programs.

    ## Custom $T$ gate injection

    As as example, the following program defines and uses a custom magic injection function that performs QEC cycles before injection.
    """)
    return


@app.cell
def _():
    from guppylang import guppy
    from guppylang.std.platform import output

    import guppyft.code.steane.logical as steane_logical

    @guppy
    def custom_t(q: steane_logical.Qubit) -> None:
        """Custom T injection gadget with QEC cycles before injection."""
        magic = steane_logical.prep_t_state()
        steane_logical.qec_cycle(magic)
        steane_logical.qec_cycle(q)
        steane_logical.inject_t(q, magic)

    @guppy
    def custom_t_example() -> None:
        q = steane_logical.Qubit()  # Logical |0>
        steane_logical.h(q)  # Logical |+>
        # Apply 4 T gates, thus acting as a Z gate in total
        for _ in range(4):
            custom_t(q)
        # Apply an X measurement
        steane_logical.h(q)
        meas = steane_logical.measure_z(q)
        # The expected result is 1
        output("result", meas.decode())

    return custom_t_example, guppy, output, steane_logical


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    When we compile this program, we obtain a [HUGR](https://github.com/Quantinuum/hugr) (the IR of the Quantinuum compiler ecosystem) that is built out of the HUGR extension of this QEC architecture.
    Then, we can call the [`implement_ops()`](https://docs.quantinuum.com/guppy/ft/api/generated/guppyft.code.steane.encode.SteaneInstance.html#guppyft.code.steane.encode.SteaneInstance.implement_ops) method from a QEC architecture instance to replace the opaque logical definitions with calls to their physical implementations.
    """)
    return


@app.cell
def _(custom_t_example):
    from guppyft.code.steane.encode import SteaneBuilder

    # Compile the program
    logical_pkg = custom_t_example.compile()

    # Create an instance of a Steane architecture and use it to produce a runnable program
    steane_arch = SteaneBuilder.new(n_blocks=3).build()
    physical_pkg = steane_arch.implement_ops(logical_pkg)
    return SteaneBuilder, physical_pkg


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The resulting `physical_pkg` is ready to be emulated locally or submitted through the Nexus Console (either for emulation or to run on a device). We show local emulation here:
    """)
    return


@app.cell
def _(physical_pkg):
    from guppylang.emulator import EmulatorBuilder

    _out = (
        EmulatorBuilder().build(
            physical_pkg, n_qubits=22
        )  # Uses statevector simulation by default
    ).run()

    print(_out.collated_shots())
    return (EmulatorBuilder,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Benefitting from automation

    Programs written at the logical level can still benefit from automated QEC cycle insertion and parallel state factories.

    Below is an example of quantum teleportation written directly using Steane logical operations.
    """)
    return


@app.cell
def _(guppy, output, steane_logical):
    @guppy
    def steane_teleport() -> None:
        # State to be teleported
        src = steane_logical.Qubit()

        # Create Bell pair
        tmp = steane_logical.Qubit()
        tgt = steane_logical.Qubit()
        steane_logical.h(tmp)
        steane_logical.cx(tmp, tgt)

        # Teleport
        steane_logical.cx(src, tmp)
        steane_logical.h(src)

        if steane_logical.measure_z(src).decode():
            steane_logical.z(tgt)
        if steane_logical.measure_z(tmp).decode():
            steane_logical.x(tgt)

        output("tgt", steane_logical.measure_z(tgt).decode())

    return (steane_teleport,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We can define two Steane architecture instances, one with default parameters, and another configured to use parallel state factories and QEC cycle insertion.
    """)
    return


@app.cell
def _(SteaneBuilder):
    from guppyft.code.steane.encode import QECPolicy, QECStyle, RUSStateFactoryConf

    # Define a QEC policy using Knill style syndrome extraction
    # We set the threshold to be 2.
    # Both the logical `H` and `CX` gates each have a cost of 1.
    qec_policy = QECPolicy(style=QECStyle.Knill, threshold=2)
    qec_policy.costs.h = 1.0
    qec_policy.costs.cx = 1.0

    # Define the state factory configuration.
    # Our factory will prepare 2 states in parallel,
    # and make 5 RUS attempts for each state.
    factory_conf = RUSStateFactoryConf(size=2, max_attempts=5)

    # We can now provide the `qec_policy` to define our Steane architecture.
    configured_steane_arch = (
        SteaneBuilder.new(n_blocks=3)
        .with_qec_policy(qec_policy)
        .with_zero_factory_conf(factory_conf)
        .build()
    )

    # We also create a default Steane architecture instance for comparison
    default_steane_arch = SteaneBuilder.new(n_blocks=3).build()
    return configured_steane_arch, default_steane_arch


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The same logical `steane_teleport` Guppy program is transformed into two different physical programs depending on the architecture instance we use.
    The easiest way to observe this difference is by analysing the log of physical operations that are performed when the program is emulated.
    We can do this locally using Selene.

    We first execute the program with default configuration.
    """)
    return


@app.cell
def _(EmulatorBuilder, default_steane_arch, steane_teleport):
    from selene_sim.backends.bundled_simulators import Stim
    from selene_sim.event_hooks.instruction_log import CircuitExtractor

    # Produce the HUGR of the program using the default architecture
    _pkg = default_steane_arch.implement_ops(steane_teleport.compile())

    # Create a CircuitExtractor to log the instructions that would run on the quantum device
    _logger = CircuitExtractor()

    _out = (
        EmulatorBuilder()
        .build(_pkg, n_qubits=22)
        .with_simulator(Stim(random_seed=42))  # Use stabilizer state simulation
        .with_event_hook(_logger)
    ).run()

    default_depth = _logger.shots[0].get_user_circuit().depth_2q()
    return CircuitExtractor, Stim, default_depth


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We now do the same for the `configured_steane_arch` instance.

    In this case, the emulator needs to be provided a larger number of qubits due to Knill-style QEC cycles being inserted and state preparation producing states in batches of two.
    """)
    return


@app.cell
def _(
    CircuitExtractor,
    EmulatorBuilder,
    Stim,
    configured_steane_arch,
    steane_teleport,
):
    # Produce the HUGR of the program using the configured architecture
    _pkg = configured_steane_arch.implement_ops(steane_teleport.compile())

    # Create a CircuitExtractor to log the instructions that would run on the quantum device
    _logger = CircuitExtractor()

    _out = (
        EmulatorBuilder()
        .build(_pkg, n_qubits=43)
        .with_simulator(Stim(random_seed=42))  # Use stabilizer state simulation
        .with_event_hook(_logger)
    ).run()

    configured_depth = _logger.shots[0].get_user_circuit().depth_2q()
    return (configured_depth,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We should expect that the program that uses the configured architecture instance has larger depth, since QEC cycles are being introduced.
    """)
    return


@app.cell
def _(configured_depth, default_depth):
    print("Two-qubit depth of programs:")
    print(f"\tWithout QEC cycles: {default_depth}")
    print(f"\tWith QEC cycles: {configured_depth}")
    return


if __name__ == "__main__":
    app.run()
