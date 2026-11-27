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
    # Verifying Logical Clifford Gadgets

    Motivation: Logical Cliffords can have non-obvious implementations, especially for $k>1$ codes. We want to be able to validate implementations and catch bugs in our logical gadgets.

    For example, see Table 2 from [Simple logical quantum computation with concatenated symplectic double codes](https://arxiv.org/pdf/2510.18753). Below is a section of this table that shows the physical implementation and logical action for
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.image(
        mo.notebook_dir() / "images" / "non_css_4_2_2_logical_cliffords1.png",
        alt="Physical implementations and logical actions for the non-CSS code",
        width=240,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    * The [`guppyft.verify`](https://docs.quantinuum.com/guppy/ft/api/generated/guppyft.verify.html#guppyft.verify) module checks logical Clifford semantics against physical implementation, using the [`valid_clifford_implementation()`](https://docs.quantinuum.com/guppy/ft/api/generated/guppyft.verify.valid_clifford_implementation.html#guppyft.verify.valid_clifford_implementation) function.
    * The tool works for $k>1$ codes and also operations between two code blocks.
    * This approach is fairly general and works for any stabilizer code. Includes non-CSS codes.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We will specify the logical semantics with a Guppy function which acts on an array of $k$ qubits. Let's see an example for the $[[7, 1, 3]]$ Steane code. The action of a logical Hadamard in the Steane code is as follows...
    """)
    return


@app.cell
def _():
    from guppylang import guppy
    from guppylang.std.builtins import array
    from guppylang.std.quantum import h, qubit

    @guppy
    def steane_specify_h(qs: array[qubit, 1]) -> None:
        h(qs[0])

    return array, guppy, h, qubit, steane_specify_h


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We can provide the implementation of the logical operation as a function which acts on an array of $n$ *physical* qubits.
    """)
    return


@app.cell
def _(array, guppy, h, qubit):
    @guppy
    def steane_impl_h(block: array[qubit, 7]) -> None:
        for i in range(len(block)):
            h(block[i])

    return (steane_impl_h,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The verifier then calculates the Clifford tableau of both of them, and checks that they are equivalent. Since the logical specification is in terms of $k$ logical qubits and the implementation is in terms of $n$ physical qubits, we need to expand the tableau of $k$ logical qubits to $n$ physical, using the definition of the stabilizer code. The definition of the stabilizer code tells us how to replace a logical Pauli with its physical Pauli string realization, as well as which additional Pauli strings we need to introduce to account for the code's stabilizer group.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Providing the stabilizer code definition

    Before we can get to verifying logical Cliffords, we need a way to specify the key properties of a stabilizer code. We provide a [`StabilizerCode`](https://docs.quantinuum.com/guppy/ft/api/generated/guppyft.code_def.StabilizerCode.html#guppyft.code_def.StabilizerCode) dataclass which specifies the $[[n, k, d]]$ code parameters as integers as well as the stabilizer generators and logical operators.

    ```python
    @dataclass(frozen=True)
    class StabilizerCode:
        n_physical_qubits: int
        n_logical_qubits: int
        distance: int
        generators: pauli.SignTermSet
        x_logicals: pauli.SignTerms
        z_logicals: pauli.SignTerms
    ```

    The stabilizer generators and logical operators are represented using types from [Zixy](https://github.com/Quantinuum/zixy), a library which provides memory efficient Pauli operator implementations in Rust.

    A [`StabilizerCode`](https://docs.quantinuum.com/guppy/ft/api/generated/guppyft.code_def.StabilizerCode.html#guppyft.code_def.StabilizerCode) definition can be given by specifying the fields directly. However its usually easier to use the [`from_python_strings()`](https://docs.quantinuum.com/guppy/ft/api/generated/guppyft.code_def.StabilizerCode.html#guppyft.code_def.StabilizerCode.from_python_strings) utility method.

    Let's provide definitions for the Steane code.
    """)
    return


@app.cell
def _():
    from guppyft.code_def import StabilizerCode

    STEANE_DEF = StabilizerCode.from_python_strings(
        n_physical_qubits=7,
        n_logical_qubits=1,
        distance=3,
        generators=["XXXXIII", "IXXIXXI", "IIXXIXX", "ZZZZIII", "IZZIZZI", "IIZZIZZ"],
        x_logicals=["XXXXXXX"],
        z_logicals=["ZZZZZZZ"],
    )
    return STEANE_DEF, StabilizerCode


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We can also provide a code definition for the non-CSS $[[4, 2, 2]]$ code which is discussed in the paper entitled "Simple logical quantum computation with concatenated symplectic double codes" (N. Berthusen and E. Durso-Sabina - https://arxiv.org/pdf/2510.18753)

    With non-CSS codes, each stabilizer generator can be made ofa mixture of $X$ and $Z$ operators. The same is true of the logical operators.
    """)
    return


@app.cell
def _(StabilizerCode):
    NON_CSS_4_2_2 = StabilizerCode.from_python_strings(
        n_physical_qubits=4,
        n_logical_qubits=2,
        distance=2,
        generators=["XZZX", "ZXXZ"],
        x_logicals=["ZIXI", "IZIX"],
        z_logicals=["IZZI", "ZIIZ"],
    )
    return (NON_CSS_4_2_2,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    There is some basic `__post_init__` validation to check we are providing reasonable [`StabilizerCode`](https://docs.quantinuum.com/guppy/ft/api/generated/guppyft.code_def.StabilizerCode.html#guppyft.code_def.StabilizerCode) definitions.

    For example, all of the stabilizer generators must commute with one another. If they do not mutually commute, then the code definition is rejected.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Verifying the implementation of logical Cliffords

    Now we can get on to verifying logical operations. We'll start by verifying some operations functions in the Steane code. This is done with the [`valid_clifford_implementation()`](https://docs.quantinuum.com/guppy/ft/api/generated/guppyft.verify.valid_clifford_implementation.html#guppyft.verify.valid_clifford_implementation) function.
    """)
    return


@app.cell
def _():
    from guppyft.verify import valid_clifford_implementation

    return (valid_clifford_implementation,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Basic examples for the Steane code
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    First, let's check the logical Hadamard implementation we defined above.
    """)
    return


@app.cell
def _(
    STEANE_DEF,
    steane_impl_h,
    steane_specify_h,
    valid_clifford_implementation,
):
    valid_clifford_implementation(
        steane_specify_h, steane_impl_h, STEANE_DEF
    )  # True => implementation is valid
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We can also verify operators between two code blocks. As an example, let's verify the implementation of the transversal CX in the Steane code.
    """)
    return


@app.cell
def _(array, guppy, qubit):
    from guppylang.std.quantum import cx

    @guppy
    def steane_specify_cx(
        first_block: array[qubit, 1], second_block: array[qubit, 1]
    ) -> None:
        cx(first_block[0], second_block[0])

    @guppy
    def steane_impl_cx(
        first_block: array[qubit, 7], second_block: array[qubit, 7]
    ) -> None:
        for i in range(len(first_block)):
            cx(first_block[i], second_block[i])

    return cx, steane_impl_cx, steane_specify_cx


@app.cell
def _(
    STEANE_DEF,
    steane_impl_cx,
    steane_specify_cx,
    valid_clifford_implementation,
):
    valid_clifford_implementation(
        steane_specify_cx, steane_impl_cx, STEANE_DEF
    )  # Transversal CX impl is valid.
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We can also detect invalid implementations. If we try to implement a logical $S$ gate in the Steane code by applying physical $S$ across across all seven physical qubits, we get `False` indicating that our implementation of logical $S$ is wrong.
    """)
    return


@app.cell
def _(STEANE_DEF, array, guppy, qubit, valid_clifford_implementation):
    from guppylang.std.quantum import s

    @guppy
    def steane_specify_s(block: array[qubit, 1]) -> None:
        s(block[0])

    @guppy
    def steane_impl_s_incorrect(block: array[qubit, 7]) -> None:
        for i in range(len(block)):
            s(block[i])

    valid_clifford_implementation(
        steane_specify_s, steane_impl_s_incorrect, STEANE_DEF
    )  # Invalid!
    return (steane_specify_s,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    It turns out the correct way to implement logical $S$ in the Steane code is by applying $S^\dagger$ across the physical qubits.
    """)
    return


@app.cell
def _(
    STEANE_DEF,
    array,
    guppy,
    qubit,
    steane_specify_s,
    valid_clifford_implementation,
):
    from guppylang.std.quantum import sdg

    @guppy
    def steane_impl_s_corrected(block: array[qubit, 7]) -> None:
        for i in range(len(block)):
            sdg(block[i])

    valid_clifford_implementation(
        steane_specify_s, steane_impl_s_corrected, STEANE_DEF
    )  # Now valid!
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Examples for $k>1$ codes
    So far, the examples with the Steane code have just been simple transversal operations. However, logical Clifford operations for $k > 1$ codes can also be verified. Let's consider the $k = 2$ CSS $[[ 4 , 2 , 2 ]]$ code to see this
    """)
    return


@app.cell
def _(StabilizerCode):
    CSS_4Q_DEF = StabilizerCode.from_python_strings(
        n_physical_qubits=4,
        n_logical_qubits=2,
        distance=2,
        generators=["XXXX", "ZZZZ"],
        x_logicals=["XXII", "XIXI"],
        z_logicals=["IZIZ", "IIZZ"],
    )
    return (CSS_4Q_DEF,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    In this $[[4, 2, 2]]$ code, we can implement a logical CX gate (intrablock) by simply swapping the physical qubits.
    """)
    return


@app.cell
def _(array, cx, guppy, qubit):
    from guppylang.std.mem import mem_swap

    @guppy
    def specify_intra_block_cx(block: array[qubit, 2]) -> None:
        cx(block[0], block[1])

    @guppy
    def implement_intra_block_cx(block: array[qubit, 4]) -> None:
        mem_swap(block[3], block[1])

    return implement_intra_block_cx, mem_swap, specify_intra_block_cx


@app.cell
def _(
    CSS_4Q_DEF,
    implement_intra_block_cx,
    specify_intra_block_cx,
    valid_clifford_implementation,
):
    valid_clifford_implementation(
        specify_intra_block_cx, implement_intra_block_cx, CSS_4Q_DEF
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We can also verify the implementation of logical SWAP in the non-CSS $[[4, 2, 2]]$ code. This is implemented by applying the Hadamard gate to all of the physical qubits.
    """)
    return


@app.cell
def _(array, guppy, h, mem_swap, qubit):
    @guppy
    def specify_swap_non_css(block: array[qubit, 2]) -> None:
        mem_swap(block[0], block[1])

    @guppy
    def implement_swap_non_css(block: array[qubit, 4]) -> None:
        for i in range(len(block)):
            h(block[i])

    return implement_swap_non_css, specify_swap_non_css


@app.cell
def _(
    NON_CSS_4_2_2,
    implement_swap_non_css,
    specify_swap_non_css,
    valid_clifford_implementation,
):
    valid_clifford_implementation(
        specify_swap_non_css,
        implement_swap_non_css,
        NON_CSS_4_2_2,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Verifying preparation of logical Pauli eigenstates
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The testing framework also allows us to verify state preparation. For example we can check preparation of logical
    $|0\rangle$ $\big(|0\rangle_{L}\big)$ in the $[[4, 2, 2]]$ code as follows.
    """)
    return


@app.cell
def _(array, cx, guppy, h, qubit):
    from guppyft.verify import valid_stabilizer_state_preparation

    @guppy
    def specify_zero_state() -> array[qubit, 2]:
        return array(qubit() for _ in range(2))

    @guppy
    def implement_non_ft_zero_state() -> array[qubit, 4]:
        block = array(qubit() for _ in range(4))

        h(block[0])
        cx(block[0], block[1])
        cx(block[0], block[2])
        cx(block[0], block[3])
        return block

    return (
        implement_non_ft_zero_state,
        specify_zero_state,
        valid_stabilizer_state_preparation,
    )


@app.cell
def _(
    CSS_4Q_DEF,
    implement_non_ft_zero_state,
    specify_zero_state,
    valid_stabilizer_state_preparation,
):
    valid_stabilizer_state_preparation(
        specify_zero_state, implement_non_ft_zero_state, CSS_4Q_DEF
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Explaining the verifier step by step

    Let's go back to the logical Hadamard in Steane. How do we work out that logical Hadamard can be implemented by broadcasting a Hadamard gate across all seven physical qubits?

    Firstly we calculate the stabilizers of a $2k$ qubit Choi state which encodes the logical Hadamard.
    """)
    return


@app.cell
def _(STEANE_DEF, steane_specify_h):
    from guppyft.code_def import _identity_code
    from guppyft.verify._expansion import get_expanded_stabilizer_set
    from guppyft.verify._verify import (
        _compute_stabilizers_single_block_unitary as compute_stabilizers_single_block_unitary,
    )

    # Get the 2k stabilizers for the 2k qubit Choi state encoding the logical operation.
    semantic_choi_stabilizers = compute_stabilizers_single_block_unitary(
        code=_identity_code(k=1),
        clifford_func=steane_specify_h,
        num_selene_qubits=2 * STEANE_DEF.n_logical_qubits,
    )
    semantic_choi_stabilizers.to_dataframe()
    return (
        compute_stabilizers_single_block_unitary,
        get_expanded_stabilizer_set,
        semantic_choi_stabilizers,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Notice how the stabilizers are closely related to the stabilizers of the Bell state $\{X_0X_1, Z_0Z_1\}$ but with a logical Hadamard applied to $X_1$ and $Z_1$.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Next, we expand the $2k$ logical stabilizers to $2k$ stabilizers of size $2n$.
    We also add the $2(n-k)$ stabilizer generators of our code.
    For each code block there are $n-k$ generators, so $2$ blocks give us $2(n-k)$.
    We have $2k + 2(n-k) = 2n$ stabilizers in total.

    We perform this expansion using the definition of the logical operators for the particular [`StabilizerCode`](https://docs.quantinuum.com/guppy/ft/api/generated/guppyft.code_def.StabilizerCode.html#guppyft.code_def.StabilizerCode) we are working with. For the Steane code, we do the following expansion:

    $$
    X_L \mapsto XXXXXXX\, \qquad Z_L \mapsto ZZZZZZZ\,.
    $$
    """)
    return


@app.cell
def _(STEANE_DEF, get_expanded_stabilizer_set, semantic_choi_stabilizers):
    expanded_semantic_stabilizers = get_expanded_stabilizer_set(
        semantic_choi_stabilizers, STEANE_DEF, num_blocks=2
    )

    expanded_semantic_stabilizers.to_dataframe()
    return (expanded_semantic_stabilizers,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    In order test two tableaux for equality, we have to convert to a suitable normal form. This is because two tableaux which look different can be equivalent up to multiplication by a Pauli stabilizer. We canonicalize the tableaux using the [SignTerms.canonicalize_all()](https://quantinuum.github.io/zixy/generated/zixy.qubit.pauli.SignTerms.html#zixy.qubit.pauli.SignTerms.canonicalize_all) method which uses a process similar to Gaussian elimination.
    """)
    return


@app.cell
def _(expanded_semantic_stabilizers):
    canonical_semantic_stabilizers = expanded_semantic_stabilizers.clone()
    canonical_semantic_stabilizers.canonicalize_all()  # Canonicalize Clifford tableau
    canonical_semantic_stabilizers.to_dataframe()
    return (canonical_semantic_stabilizers,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now we calculate the $2n$ stabilizers of the Choi state encoding the $n$ qubit implementation of the logical operation. In this case, the physical Hadamard acts on seven qubits. Therefore we expect our implementation tableau to contain $2*7 =14$ Pauli stabilizers.
    """)
    return


@app.cell
def _(STEANE_DEF, compute_stabilizers_single_block_unitary, steane_impl_h):
    # Calculate the 2n stabilizers of the Choi state encoding the physical operation.
    implementation_stabilizers = compute_stabilizers_single_block_unitary(
        STEANE_DEF, steane_impl_h, num_selene_qubits=2 * (STEANE_DEF.n_physical_qubits)
    )
    implementation_stabilizers.to_dataframe()
    return (implementation_stabilizers,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We now canonicalize these implementation stabilizers as we did above for the semantic stabilizers.
    """)
    return


@app.cell
def _(implementation_stabilizers):
    canonical_implementation_stabilizers = implementation_stabilizers.clone()
    canonical_implementation_stabilizers.canonicalize_all()  # Canonicalize Clifford tableau
    canonical_implementation_stabilizers.to_dataframe()
    return (canonical_implementation_stabilizers,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now that we have two Clifford tableaux in a suitable normal form, we can test them for equality.
    """)
    return


@app.cell
def _(canonical_implementation_stabilizers, canonical_semantic_stabilizers):
    canonical_semantic_stabilizers == canonical_implementation_stabilizers
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Summary of available features

    The following features are available for verification of Clifford operations with [`valid_clifford_implementation()`](https://docs.quantinuum.com/guppy/ft/api/generated/guppyft.verify.valid_clifford_implementation.html#guppyft.verify.valid_clifford_implementation)

    * Works for $k>1$ codes
    * Works for operations on a single logical block or between two logical blocks
    * Works for non-CSS codes (e.g. the $[[5, 1, 3]]$ code)
    * Ancilla qubits can be used in the implementation

    The features above are also available in [`valid_stabilizer_state_preparation()`](https://docs.quantinuum.com/guppy/ft/api/generated/guppyft.verify.valid_stabilizer_state_preparation.html#guppyft.verify.valid_stabilizer_state_preparation) which can be used to verify the preparation of logical Pauli eigenstates (e.g. $|0\rangle_L$, $|+\rangle_L$)
    """)
    return


if __name__ == "__main__":
    app.run()
