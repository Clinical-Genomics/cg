from cg.constants.pedigree import Pedigree
from cg.services.order_validation_service.models.errors import (
    DescendantAsFatherError,
    DescendantAsMotherError,
    PedigreeError,
    SampleIsOwnFatherError,
    SampleIsOwnMotherError,
)
from cg.services.order_validation_service.workflows.tomte.validation.inter_field.pedigree.models import (
    FamilyTree,
    Node,
)


def validate_tree(pedigree: FamilyTree) -> list[PedigreeError]:
    errors = []
    for node in pedigree.nodes:
        if not node.visited:
            detect_cycles(node=node, errors=errors)
    return errors


def detect_cycles(node: Node, errors: list[PedigreeError]) -> None:
    """Detect cycles in the pedigree graph using depth-first search"""
    node.visited = True
    node.in_current_path = True

    parents = {Pedigree.MOTHER: node.mother, Pedigree.FATHER: node.father}

    for parent_type, parent in parents.items():
        if parent and parent.in_current_path:
            error = get_error(node=node, parent_type=parent_type)
            errors.append(error)
        elif parent and not parent.visited:
            detect_cycles(node=parent, errors=errors)

    node.in_current_path = False


def get_error(node: Node, parent_type: str) -> PedigreeError:
    if parent_type == Pedigree.MOTHER:
        return get_mother_error(node)
    if parent_type == Pedigree.FATHER:
        return get_father_error(node)


def get_mother_error(node: Node) -> PedigreeError:
    sample = node.sample
    if sample.name == sample.mother:
        return SampleIsOwnMotherError(sample_name=sample.name, case_name=node.case_name)
    return DescendantAsMotherError(sample_name=sample.name, case_name=node.case_name)


def get_father_error(node: Node) -> PedigreeError:
    sample = node.sample
    if sample.name == sample.father:
        return SampleIsOwnFatherError(sample_name=sample.name, case_name=node.case_name)
    return DescendantAsFatherError(sample_name=sample.name, case_name=node.case_name)
