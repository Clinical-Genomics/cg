from cg.services.order_validation_service.models.errors import PedigreeError
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase
from cg.services.order_validation_service.workflows.tomte.validation.inter_field.pedigree.models import (
    FamilyTree,
)
from cg.services.order_validation_service.workflows.tomte.validation.inter_field.pedigree.utils import (
    validate_tree,
)


def get_pedigree_errors(case: TomteCase) -> list[PedigreeError]:
    pedigree = FamilyTree(case)
    return validate_tree(pedigree)
