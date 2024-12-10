from cg.services.order_validation_service.errors.case_sample_errors import PedigreeError
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase
from cg.services.order_validation_service.rules.case_sample.pedigree.models import FamilyTree
from cg.services.order_validation_service.rules.case_sample.pedigree.utils import validate_tree


def get_pedigree_errors(case: TomteCase, case_index: int) -> list[PedigreeError]:
    pedigree = FamilyTree(case=case, case_index=case_index)
    return validate_tree(pedigree)
