from hugr.package import Package


def mark_qubits_for_dynamic_allocation(
    pkg: Package,
) -> Package:
    """
    Marks all remaining `tket.quantum.QAlloc` operations in the given single-HUGR
    package as "dynamically allocated", allowing to completely push all conversion nodes
    through the HUGR.

    WIP, and currently the identity function.
    """
    return pkg
