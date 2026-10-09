from collections import defaultdict
from typing import no_type_check

from guppylang import guppy
from guppylang.library import link_name
from guppylang.std.angles import angle
from guppylang.std.builtins import array, comptime, owned, result
from guppylang.std.collections import Stack
from guppylang.std.option import Option, nothing, some
from guppylang.std.ptr import Ptr
from guppylang.std.qsystem import zz_phase
from guppylang.std.quantum import cx, discard, measure, project_z, qubit, x

from guppyft.encode import EncodeSpec, ImplementOps, ImplementOpsSpec, OpReplacements
from guppyft.globals import map_global, with_global

N = guppy.nat_var("N")


def identity_code_spec(
    n_qubits: int, qec_budget: int = 1, costs: dict[str, int] | None = None
) -> EncodeSpec:
    costs = costs or defaultdict(int)

    @guppy.struct
    class BlockData:
        physical: Option[qubit]
        qec_counter: int

    @guppy.struct
    class Global:
        # Data-cell registry permits idle-QEC scans without owning LogicalBlock
        # cells: BlockData has no back-reference, so this graph is acyclic.
        blocks: array[Ptr[BlockData], comptime(n_qubits)]
        free_ids: Stack[int, comptime(n_qubits)]

    @guppy.struct
    class LogicalBlock:
        data: Ptr[BlockData]
        global_state: Ptr[Global]
        slot: int

    @guppy
    @no_type_check
    def inspect_block(
        block: Ptr[LogicalBlock],
    ) -> tuple[Ptr[BlockData], Ptr[Global], int]:
        @guppy
        def inspect(
            b: LogicalBlock @ owned, unused: None
        ) -> tuple[LogicalBlock, tuple[Ptr[BlockData], Ptr[Global], int]]:
            handles = b.data.copy(), b.global_state.copy(), b.slot
            return b, handles

        return block.map(inspect, None)

    @guppy
    @no_type_check
    def take(data: Ptr[BlockData]) -> qubit:
        @guppy
        def impl(b: BlockData @ owned, unused: None) -> tuple[BlockData, qubit]:
            q = b.physical.take().unwrap()
            return b, q

        return data.map(impl, None)

    @guppy
    @no_type_check
    def put(data: Ptr[BlockData], q: qubit @ owned) -> None:
        @guppy
        def impl(b: BlockData @ owned, q: qubit @ owned) -> tuple[BlockData, None]:
            b.physical.swap(some(q)).unwrap_nothing()
            return b, None

        data.map(impl, q)

    @guppy
    @no_type_check
    def read_counter(data: Ptr[BlockData]) -> int:
        @guppy
        def impl(b: BlockData @ owned, unused: None) -> tuple[BlockData, int]:
            counter = b.qec_counter
            return b, counter

        return data.map(impl, None)

    @guppy
    @no_type_check
    def qec_policy(
        global_state: Ptr[Global],
        active: array[int, N] @ owned,
        cost_op: int,
        cost_idle: int,
    ) -> None:
        charges = array(cost_idle for _ in range(comptime(n_qubits)))
        for i in active:
            charges[i] = cost_op

        @guppy
        def policy(
            g: Global @ owned, charges: array[int, comptime(n_qubits)] @ owned
        ) -> tuple[Global, None]:
            @guppy
            def charge(b: BlockData @ owned, cost: int) -> tuple[BlockData, bool]:
                b.qec_counter += cost
                due = b.qec_counter >= comptime(qec_budget)
                return b, due

            @guppy
            def reset(b: BlockData @ owned, unused: None) -> tuple[BlockData, None]:
                b.qec_counter = 0
                return b, None

            for i in range(comptime(n_qubits)):
                if g.blocks[i].map(charge, charges[i]):
                    counters = array(
                        read_counter(g.blocks[j]) for j in range(comptime(n_qubits))
                    )
                    result("qec_counter", counters)
                    g.blocks[i].map(reset, None)
            return g, None

        global_state.map(policy, charges)

    @guppy
    @no_type_check
    def release(block: Ptr[LogicalBlock] @ owned) -> None:
        b = block.free().unwrap()
        b.data.free().unwrap_nothing()
        b.global_state.free().unwrap_nothing()

    @guppy
    @no_type_check
    def clone_global(state: Ptr[Global] @ owned) -> tuple[Ptr[Global], Ptr[Global]]:
        clone = state.copy()
        return state, clone

    @guppy
    @link_name("link.identity.QAlloc")
    @no_type_check
    def _QAlloc() -> Ptr[LogicalBlock]:
        global_state = map_global(clone_global)

        @guppy
        def allocate(
            g: Global @ owned, unused: None
        ) -> tuple[Global, tuple[Ptr[BlockData], int]]:
            result("_QAlloc", 0)
            if len(g.free_ids) == 0:
                exit("get_next_addr: No more qubits to allocate")
            slot = g.free_ids.pop()
            data = g.blocks[slot].copy()
            put(data, qubit())
            return g, (data, slot)

        data, slot = global_state.map(allocate, None)
        return Ptr(LogicalBlock(data, global_state, slot))

    @guppy
    @no_type_check
    def free_slot(global_state: Ptr[Global], slot: int) -> None:
        @guppy
        def impl(g: Global @ owned, slot: int) -> tuple[Global, None]:
            g.free_ids.push(slot)
            return g, None

        global_state.map(impl, slot)

    @guppy
    @link_name("link.identity.MeasureFree")
    @no_type_check
    def _MeasureFree(block: Ptr[LogicalBlock] @ owned) -> bool:
        result("_MeasureFree", 0)
        data, global_state, slot = inspect_block(block)
        res = measure(take(data)).read()
        free_slot(global_state, slot)
        data.free().unwrap_nothing()
        global_state.free().unwrap_nothing()
        release(block)
        return res

    @guppy
    @link_name("link.identity.Measure")
    @no_type_check
    def _Measure(block: Ptr[LogicalBlock] @ owned) -> tuple[Ptr[LogicalBlock], bool]:
        result("_Measure", 0)
        data, global_state, _slot = inspect_block(block)
        q = take(data)
        res = project_z(q).read()
        put(data, q)
        data.free().unwrap_nothing()
        global_state.free().unwrap_nothing()
        return block, res

    @guppy
    @link_name("link.identity.QFree")
    @no_type_check
    def _QFree(block: Ptr[LogicalBlock] @ owned) -> None:
        result("_QFree", 0)
        data, global_state, slot = inspect_block(block)
        discard(take(data))
        free_slot(global_state, slot)
        data.free().unwrap_nothing()
        global_state.free().unwrap_nothing()
        release(block)

    @guppy
    @link_name("link.identity.X")
    @no_type_check
    def _X(block: Ptr[LogicalBlock] @ owned) -> Ptr[LogicalBlock]:
        result("_X", 0)
        data, global_state, slot = inspect_block(block)
        q = take(data)
        x(q)
        put(data, q)
        qec_policy(
            global_state, array(slot), comptime(costs["X"]), comptime(costs["IDLE_X"])
        )
        data.free().unwrap_nothing()
        global_state.free().unwrap_nothing()
        return block

    @guppy
    @link_name("link.identity.CX")
    @no_type_check
    def _CX(
        ctl: Ptr[LogicalBlock] @ owned, tgt: Ptr[LogicalBlock] @ owned
    ) -> tuple[Ptr[LogicalBlock], Ptr[LogicalBlock]]:
        result("_CX", 0)
        cd, cg, ci = inspect_block(ctl)
        td, tg, ti = inspect_block(tgt)
        cq, tq = take(cd), take(td)
        cx(cq, tq)
        put(cd, cq)
        put(td, tq)
        qec_policy(cg, array(ci, ti), comptime(costs["CX"]), comptime(costs["IDLE_CX"]))
        cd.free().unwrap_nothing()
        td.free().unwrap_nothing()
        cg.free().unwrap_nothing()
        tg.free().unwrap_nothing()
        return ctl, tgt

    @guppy
    @link_name("link.identity.ZZPhase")
    @no_type_check
    def _ZZPhase(
        ctl: Ptr[LogicalBlock] @ owned, tgt: Ptr[LogicalBlock] @ owned, phase: float
    ) -> tuple[Ptr[LogicalBlock], Ptr[LogicalBlock]]:
        result("_ZZPhase", 0)
        cd, cg, ci = inspect_block(ctl)
        td, tg, ti = inspect_block(tgt)
        cq, tq = take(cd), take(td)
        zz_phase(cq, tq, angle(phase))
        put(cd, cq)
        put(td, tq)
        qec_policy(
            cg,
            array(ci, ti),
            comptime(costs["ZZPhase"]),
            comptime(costs["IDLE_ZZPhase"]),
        )
        cd.free().unwrap_nothing()
        td.free().unwrap_nothing()
        cg.free().unwrap_nothing()
        tg.free().unwrap_nothing()
        return ctl, tgt

    @guppy
    @link_name("link.identity.Read")
    def _Read(m: bool) -> bool:
        return m

    ops = OpReplacements().with_funcs(
        {
            ("tket.quantum", "QAlloc"): _QAlloc,
            ("tket.measurement", "Read"): _Read,
            ("tket.quantum", "MeasureFree"): _MeasureFree,
            ("tket.quantum", "Measure"): _Measure,
            ("tket.quantum", "QFree"): _QFree,
            ("tket.quantum", "X"): _X,
            ("tket.quantum", "CX"): _CX,
            ("tket.qsystem", "ZZPhase"): _ZZPhase,
            ("tket.quantum", "ZZPhase"): _ZZPhase,
            ("tket.qsystem.helios", "ZZPhase"): _ZZPhase,
            ("tket.qsystem.sol", "ZZPhase"): _ZZPhase,
        }
    )

    def build_wrapper(func):
        @guppy
        @no_type_check
        def wrapper() -> None:
            global_state = Ptr(
                Global(
                    array(
                        Ptr(BlockData(nothing[qubit](), 0))
                        for _ in range(comptime(n_qubits))
                    ),
                    Stack(
                        array(some(i) for i in range(comptime(n_qubits))),
                        comptime(n_qubits),
                    ),
                )
            )
            global_state = with_global(global_state, func)
            g = global_state.free().unwrap()
            for data in g.blocks:
                b = data.free().unwrap()
                if b.physical.is_some():
                    discard(b.physical.unwrap())
                else:
                    b.physical.unwrap_nothing()

        return wrapper

    return EncodeSpec(
        implement_ops=ImplementOps.for_spec(
            ImplementOpsSpec(
                ops=ops,
                build_wrapper=build_wrapper,
            )
        )
    )
