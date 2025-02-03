from cg.services.orders.validation.errors.case_sample_errors import PedigreeError
from cg.services.orders.validation.rules.case_sample.pedigree.models import FamilyTree
from cg.services.orders.validation.rules.case_sample.pedigree.utils import validate_tree
from cg.services.orders.validation.workflows.mip_dna.models.case import MipDnaCase
from cg.services.orders.validation.workflows.tomte.models.case import TomteCase
from cg.store.store import Store


def get_pedigree_errors(
    case: TomteCase | MipDnaCase, case_index: int, store: Store
) -> list[PedigreeError]:
    """Return a list of errors if any sample is labelled as its own ancestor in the family tree."""
    pedigree = FamilyTree(case=case, case_index=case_index, store=store)
    return validate_tree(pedigree)
