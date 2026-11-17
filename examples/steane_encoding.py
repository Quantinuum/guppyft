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
    # Automatic Encoding for the Steane Code

    Guppy FT is an extension of the Guppy quantum programming language to aid writing, compiling and running fault-tolerant programs by providing a separation of concerns between writing quantum algorithms and quantum error correction (QEC). Researchers are able to write QEC-agnostic programs, and utilize QEC code architectures developed by experts to automatically encode into an error-protected program.

    This notebook provides an introduction to the encoding features of Guppy FT through simple examples.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Encoding a Guppy program

    Encoding happens in four stages:
    1. Write a computational Guppy program using [`guppylang.std.quantum`](https://docs.quantinuum.com/guppy/api/generated/guppylang.std.quantum.html#guppylang.std.quantum) operations.
    2. Run an encoding pass to convert the computational program into a logical program.
    3. (Optional) Run logical-aware optimization passes.
    4. Replace the logical operations with physical implementations.

    Let's see a full workflow with a quantum teleportation program.
    """)
    return


@app.cell
def _():
    from guppylang import guppy
    from guppylang.std import quantum as qlib
    from guppylang.std.builtins import array, owned
    from guppylang.std.platform import output

    return array, guppy, output, owned, qlib


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    First, we write our computational program. At this stage, we are not concerned with QEC. The program is written assuming that it will run on a noiseless quantum computer using [`guppylang.std`](https://docs.quantinuum.com/guppy/api/generated/guppylang.std.html#guppylang.std) operations.
    """)
    return


@app.cell
def _(guppy, output, owned, qlib):
    @guppy
    def teleport_primitive(src: qlib.qubit @ owned) -> qlib.qubit:
        # Create Bell pair
        tmp = qlib.qubit()
        tgt = qlib.qubit()
        qlib.h(tmp)
        qlib.cx(tmp, tgt)

        # Teleport
        qlib.cx(src, tmp)
        qlib.h(src)
        if qlib.measure(src).read():
            qlib.z(tgt)
        if qlib.measure(tmp).read():
            qlib.x(tgt)

        return tgt

    @guppy
    def teleport() -> None:
        # Qubit to be teleported
        src = qlib.qubit()

        # Teleport `src` to `tgt`
        tgt = teleport_primitive(src)
        output("tgt", qlib.measure(tgt).read())

    return teleport, teleport_primitive


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now we can define the QEC code architecture that we would use to encode our program to be fault-tolerant. An architecture includes the necessary encoding and implementation passes to convert our computational program into a runnable, physical package.

    For this example, we will use the Steane architecture.
    """)
    return


@app.cell
def _():
    from guppyft.code.steane.encode import SteaneBuilder

    # Define a Steane architecture instance.
    # The only required parameter is an upper bound
    # to the total number of logical blocks available
    # during program execution.

    steane = SteaneBuilder().build(n_blocks=3)
    return SteaneBuilder, steane


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We can use our architecture to encode the program, running the full pass from computational to logical and finally to physical, producing a package that we can run.
    """)
    return


@app.cell
def _(steane, teleport):
    teleport_unencoded = teleport.compile()
    teleport_encoded = steane.encode(teleport_unencoded)
    return teleport_encoded, teleport_unencoded


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We can emulate the encoded program using Selene locally, or submit it through the Nexus Console to run on proprietary emulators or quantum devices. Here, we illustrate local emulation using Stim (a Clifford circuit simulator) and a simple depolarizing noise model.
    """)
    return


@app.cell
def _(teleport_encoded):
    from guppylang.emulator import EmulatorBuilder
    from selene_sim.backends.bundled_error_models import DepolarizingErrorModel
    from selene_sim.backends.bundled_simulators import Stim

    _results = (
        # Create an EmulatorBuilder and instantiate it with the encoded program
        EmulatorBuilder()
        .build(teleport_encoded, n_qubits=22)
        # Then, configure the emulator instance
        .with_simulator(Stim(random_seed=42))
        .with_error_model(DepolarizingErrorModel(random_seed=42, p_1q=1e-4, p_2q=1e-3))
        .with_shots(1000)
    ).run()

    print(_results.collated_counts())
    return EmulatorBuilder, Stim


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    For convenience, the Steane architecture provides an [`emulator()`](https://docs.quantinuum.com/guppy/ft/api/generated/guppyft.code.steane.encode.SteaneInstance.html#guppyft.code.steane.encode.SteaneInstance.emulator) method that automatically encodes the program and builds the emulator. See the API docs for [`emulator()`](https://docs.quantinuum.com/guppy/ft/api/generated/guppyft.code.steane.encode.SteaneInstance.html#guppyft.code.steane.encode.SteaneInstance.emulator), under [`SteaneInstance`](https://docs.quantinuum.com/guppy/ft/api/generated/guppyft.code.steane.encode.SteaneInstance.html#guppyft.code.steane.encode.SteaneInstance).

    Furthermore, we can explore the trace of operations that have been emulated. A quick check confirms that the encoded program is considerably deeper.
    """)
    return


@app.cell
def _(EmulatorBuilder, Stim, teleport_unencoded):
    from selene_sim.event_hooks.instruction_log import CircuitExtractor

    # Create a CircuitExtractor to log the instructions that would run on the quantum device
    _logger = CircuitExtractor()

    # Obtain the depth of the unencoded program
    _results = (
        EmulatorBuilder()
        .build(teleport_unencoded, n_qubits=3)
        .with_simulator(Stim(random_seed=42))  # Use stabilizer state simulation
        .with_event_hook(_logger)
    ).run()

    unencoded_depth = _logger.shots[0].get_user_circuit().depth()
    return CircuitExtractor, unencoded_depth


@app.cell
def _(CircuitExtractor, EmulatorBuilder, Stim, teleport_encoded):
    # Create a new CircuitExtractor instance
    _logger = CircuitExtractor()

    # Obtain the depth of the encoded program
    _results = (
        EmulatorBuilder()
        .build(teleport_encoded, n_qubits=22)
        .with_simulator(Stim(random_seed=42))  # Use stabilizer state simulation
        .with_event_hook(_logger)
    ).run()

    encoded_depth = _logger.shots[0].get_user_circuit().depth()
    return (encoded_depth,)


@app.cell
def _(encoded_depth, unencoded_depth):
    print("Depth (longest sequence of operations):")
    print(f"\tUnencoded program: {unencoded_depth}")
    print(f"\tEncoded program: {encoded_depth}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Dynamic allocation of logical qubits

    Guppy FT provides support for arbitrary control flow through dynamic allocation of logical qubits. Below is an example of qubits being dynamically allocated based on the outcome of a qubit measurement.
    """)
    return


@app.cell
def _(SteaneBuilder, array, guppy, output, qlib):
    @guppy
    def dynamic_allocation() -> None:
        q0 = qlib.qubit()
        qlib.h(q0)
        if qlib.measure(q0):  # If true, allocate a single qubit
            q_arr = array(qlib.qubit())
            for q in q_arr:
                output("q", qlib.measure(q).read())
        else:  # Otherwise, allocate two qubits
            q_arr = array(qlib.qubit(), qlib.qubit())
            qlib.cx(q_arr[0], q_arr[1])
            for q in q_arr:
                output("q", qlib.measure(q).read())

    _dyn_alloc_encoded = (
        SteaneBuilder().build(n_blocks=3).encode(dynamic_allocation.compile())
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Mid-circuit measurement and qubit reuse

    The Quantinuum stack supports mid-circuit measurements and qubit reuse. This support continues at the logical level with Guppy FT.

    We can demonstrate this using the `teleport_primitive` defined above to teleport a qubit twice. Without qubit reuse, this program would require 5 logical qubits. However, only 3 logical qubits are required at any one time, as demonstrated by imposing `n_blocks=3`.
    """)
    return


@app.cell
def _(SteaneBuilder, guppy, output, qlib, teleport_primitive):
    @guppy
    def qubit_reuse() -> None:
        # Qubit to teleport
        src = qlib.qubit()

        # Run teleportation twice
        tgt = teleport_primitive(src)
        src = teleport_primitive(tgt)

        output("src", qlib.measure(src).read())

    # Encode with three logical blocks to demonstrate qubit reuse.
    _reuse_encoded = SteaneBuilder().build(n_blocks=3).encode(qubit_reuse.compile())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Dynamic QEC cycle insertion

    In quantum programs with complex control flow, it can be useful to use information obtained during runtime to determine when to insert a QEC cycle. Guppy FT supports dynamic insertion of QEC cycles depending on the logical gates that have been performed.

    In this demonstration, each logical operation is assigned a cost, which is tracked on a per-block basis. At runtime, once a threshold is reached, a QEC cycle is inserted, and the tracking counter is reset to 0.
    """)
    return


@app.cell
def _(SteaneBuilder):
    from guppyft.code.steane.encode import QECPolicy, QECStyle

    # Define a QEC policy using Steane style syndrome extraction
    # We set the threshold to be 2.
    # Both the logical `H` and `CX` gates each have a cost of 1.
    qec_policy = QECPolicy(style=QECStyle.Steane, threshold=2)
    qec_policy.costs.h = 1.0
    qec_policy.costs.cx = 1.0

    # We can now provide the `qec_policy` to define our Steane architecture.
    _steane_qec = SteaneBuilder().with_qec_policy(qec_policy).build(n_blocks=2)
    return (qec_policy,)


@app.cell
def _(SteaneBuilder, guppy, output, qec_policy, qlib):
    # Demonstration program to apply `H` and `CX` gates to two qubits.
    @guppy
    def my_program() -> None:
        q0 = qlib.qubit()
        q1 = qlib.qubit()

        # Track costs:      [q0 , q1 ]
        qlib.h(q0)  #       [1.0, 0.0]
        qlib.cx(q0, q1)  #  [2.0, 1.0]
        #                   [0.0, 1.0] <-- QEC cycle on q0
        qlib.h(q1)  #       [1.0, 2.0]
        #                   [1.0, 0.0] <-- QEC cycle on q1

        output("q0", qlib.measure(q0).read())
        output("q1", qlib.measure(q1).read())

    # Encode two programs with, and without our QEC policy.
    encoded_without_qec_cycles = (
        SteaneBuilder().build(n_blocks=2).encode(my_program.compile())
    )
    encoded_with_qec_cycles = (
        SteaneBuilder()
        .with_qec_policy(qec_policy)
        .build(n_blocks=2)
        .encode(my_program.compile())
    )
    return encoded_with_qec_cycles, encoded_without_qec_cycles, my_program


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Once again, we can use Selene's `CircuitExtractor` to explore the operations that run and check that, indeed, QEC cycles were introduced.

    In this case, we count the number of measurement operations.
    """)
    return


@app.cell
def _(CircuitExtractor, EmulatorBuilder, Stim, encoded_without_qec_cycles):
    # Create a new CircuitExtractor instance
    _logger = CircuitExtractor()

    # Obtain the number of measurements executed in the case of no QEC cycles inserted
    _results = (
        EmulatorBuilder()
        .build(encoded_without_qec_cycles, n_qubits=22)
        .with_simulator(Stim(random_seed=42))  # Use stabilizer state simulation
        .with_event_hook(_logger)
    ).run()

    n_meas_no_qec = sum(
        1
        for cmd in _logger.shots[0].get_user_circuit().get_commands()
        if "Measure" in str(cmd)
    )
    return (n_meas_no_qec,)


@app.cell
def _(CircuitExtractor, EmulatorBuilder, Stim, encoded_with_qec_cycles):
    # Create a new CircuitExtractor instance
    _logger = CircuitExtractor()

    # Obtain the number of measurements executed in the case of QEC cycles inserted
    _results = (
        EmulatorBuilder()
        .build(encoded_with_qec_cycles, n_qubits=22)
        .with_simulator(Stim(random_seed=42))  # Use stabilizer state simulation
        .with_event_hook(_logger)
    ).run()

    n_meas_qec = sum(
        1
        for cmd in _logger.shots[0].get_user_circuit().get_commands()
        if "Measure" in str(cmd)
    )
    return (n_meas_qec,)


@app.cell
def _(n_meas_no_qec, n_meas_qec):
    print("Number of physical measurements performed:")
    print(f"\tWithout QEC cycles: {n_meas_no_qec}")
    print(f"\tWith QEC cycles: {n_meas_qec}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Indeed, there are 32 more physical measurements: each QEC cycle uses `(7+1)*2 = 16` physical measurements, since it prepares and measures two logical zero states (7 physical qubits, plus 1 flag ancilla), and we expect two QEC cycles to be introduced.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## State factories

    Fault-tolerant state preparation often uses a repeat-until-success (RUS) scheme that measures flag ancilla qubits to verify that the state preparation succeeds. In order to run state preparation in parallel, we need to defer reading the measurement outcome on these ancilla qubits, as described in Guppy's language guide (see [Measurement section](https://docs.quantinuum.com/guppy/language_guide/measurement.html)). Our Steane architecture defines a `StateFactory` that handles deferral of measurements and parallelizes RUS state preparation. Users can configure the parameters of the factory both for zero states and magic states.

    The following example configures an architecture instance that prepares zero states in batches of 2, making up to 5 RUS attempts per request.
    """)
    return


@app.cell
def _(SteaneBuilder, my_program, qec_policy):
    from guppyft.code.steane.encode import RUSStateFactoryConf

    # Define the state factory configuration.
    factory_conf = RUSStateFactoryConf(size=2, max_attempts=5)

    # Use the factory configuration to define our Steane architecture.
    steane_code_factories = (
        SteaneBuilder()
        .with_qec_policy(qec_policy)
        .with_zero_factory_conf(factory_conf)
        .build(n_blocks=2)
    )
    _qec_factory_encoded = steane_code_factories.encode(my_program.compile())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Some tools to visualize parallelism will be released in due time. Until then, users can explore the impact of parallelizing state preparation by running on the [Quantinuum Helios-1E emulator](https://docs.quantinuum.com/systems/user_guide/emulator_user_guide/emulators/helios_emulators.html) through the Nexus Console. Helios-1E includes memory noise and, hence, parallelization makes a positive impact on program performance thanks to a decrease in shot time.
    """)
    return


if __name__ == "__main__":
    app.run()
