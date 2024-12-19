from cg.constants.pedigree import Pedigree
from cg.services.order_validation_service.errors.case_sample_errors import (
    DescendantAsFatherError,
    DescendantAsMotherError,
    PedigreeError,
    SampleIsOwnFatherError,
    SampleIsOwnMotherError,
)
from cg.services.order_validation_service.models.existing_sample import ExistingSample
from cg.services.order_validation_service.rules.case_sample.pedigree.models import FamilyTree, Node
from cg.services.order_validation_service.workflows.mip_dna.models.sample import MipDnaSample
from cg.services.order_validation_service.workflows.tomte.models.sample import TomteSample


def validate_tree(pedigree: FamilyTree) -> list[PedigreeError]:
    errors: list[PedigreeError] = []
    for node in pedigree.nodes:
        if not node.visited:
            detect_cycles(node=node, errors=errors)
    return errors


def detect_cycles(node: Node, errors: list[PedigreeError]) -> None:
    """Detect cycles in the pedigree graph using depth-first search"""
    node.visited = True
    node.in_current_path = True

    parents: dict[str, Node] = {Pedigree.MOTHER: node.mother, Pedigree.FATHER: node.father}

    for parent_type, parent in parents.items():
        if parent and parent.in_current_path:
            error: PedigreeError = get_error(node=node, parent_type=parent_type)
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
    sample: TomteSample | MipDnaSample | ExistingSample = node.sample
    if node.sample_name == sample.mother:
        return SampleIsOwnMotherError(sample_index=node.sample_index, case_index=node.case_index)
    return DescendantAsMotherError(sample_index=node.sample_index, case_index=node.case_index)


def get_father_error(node: Node) -> PedigreeError:
    sample: TomteSample = node.sample
    if node.sample_name == sample.father:
        return SampleIsOwnFatherError(sample_index=node.sample_index, case_index=node.case_index)
    return DescendantAsFatherError(sample_index=node.sample_index, case_index=node.case_index)
