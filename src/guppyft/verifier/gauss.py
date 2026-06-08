from zixy.qubit.pauli import SignTerms, X, Y, Z


def canonicalize(tab: SignTerms) -> None:
    pivot_row = 0
    for pivot_col in range(len(tab.qubits)):
        # Solve Xs
        for i in range(pivot_row, len(tab)):
            p = tab[i].string[pivot_col]
            # Find a stabilizer to pivot on
            if p in (X, Y):
                # Guarantee that pivot_row contains X or Y
                if i != pivot_row:
                    tab[pivot_row] *= tab[i]
                # Eliminate X or Y from all other stabilizers
                for j in range(len(tab)):
                    pj = tab[j].string[pivot_col]
                    if j != pivot_row and (pj in (X, Y)):
                        tab[j] *= tab[pivot_row]
                pivot_row += 1
                break
        # Do the same for Zs
        for i in range(pivot_row, len(tab)):
            p = tab[i].string[pivot_col]
            if p == Z:
                if i != pivot_row:
                    tab[pivot_row] *= tab[i]
                for j in range(len(tab)):
                    pj = tab[j].string[pivot_col]
                    if j != pivot_row and (pj in (Z, Y)):
                        tab[j] *= tab[pivot_row]
                pivot_row += 1
                break
