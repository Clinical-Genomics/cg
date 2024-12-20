from cg.services.order_validation_service.errors.case_sample_errors import PedigreeError
from cg.services.order_validation_service.rules.case_sample.pedigree.models import FamilyTree
from cg.services.order_validation_service.rules.case_sample.pedigree.utils import validate_tree
from cg.services.order_validation_service.workflows.mip_dna.models.case import MipDnaCase
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase
from cg.store.store import Store


def get_pedigree_errors(
    case: TomteCase | MipDnaCase, case_index: int, store: Store
) -> list[PedigreeError]:
    """This method finds errors within the order's family tree. These are errors of the kind
    where a sample is marked as its own ancestor."""
    pedigree = FamilyTree(case=case, case_index=case_index, store=store)
    return validate_tree(pedigree)
