import itertools
__author__ = 'jnation'


def get_num_mol_changes(molecules):
    return len(list(itertools.groupby([mol.type.upper() for mol in molecules])))


def get_num_filter_changes(molecules):
    return len(list(itertools.groupby([mol.filter for mol in molecules])))
