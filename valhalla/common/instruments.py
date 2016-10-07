__author__ = 'jnation'


def get_num_mol_changes(molecules):
    prev_mol_type = None
    n_mol_changes = 0
    for mol in molecules:
        if mol.type.upper() != prev_mol_type:
            n_mol_changes += 1
        prev_mol_type = mol.type.upper()

    return n_mol_changes


def get_num_filter_changes(molecules):
    prev_filter = None
    n_filter_changes = 0
    for mol in molecules:
        if mol.filter and mol.filter != prev_filter:
            n_filter_changes += 1
            prev_filter = mol.filter

    return n_filter_changes
