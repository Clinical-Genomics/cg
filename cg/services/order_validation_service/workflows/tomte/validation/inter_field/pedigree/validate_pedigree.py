from cg.services.order_validation_service.models.errors import PedigreeError
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase
from cg.services.order_validation_service.workflows.tomte.validation.inter_field.pedigree.models import (
    Pedigree,
)
from cg.services.order_validation_service.workflows.tomte.validation.inter_field.pedigree.utils import (
    detect_cycles,
)


def get_pedigree_errors(case: TomteCase) -> list[PedigreeError]:
    pedigree = Pedigree(case)
    return validate(pedigree)


def validate(pedigree: Pedigree) -> list[PedigreeError]:
    errors = []
    for node in pedigree.nodes:
        if not node.visited:
            detect_cycles(node, errors)
    return errors
