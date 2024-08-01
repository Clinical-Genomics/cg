from cg.services.order_validation_service.models.errors import PedigreeError
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase
from cg.services.order_validation_service.workflows.tomte.validation.inter_field.pedigree.models import (
    Pedigree,
)


def get_pedigree_errors(case: TomteCase) -> list[PedigreeError]:
    pedigree = Pedigree(case)
    return pedigree.validate()
