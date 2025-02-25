from cg.constants.pedigree import Pedigree
from cg.services.orders.validation.errors.case_sample_errors import (
    DescendantAsFatherError,
    DescendantAsMotherError,
    PedigreeError,
    SampleIsOwnFatherError,
    SampleIsOwnMotherError,
)
from cg.services.orders.validation.models.existing_sample import ExistingSample
from cg.services.orders.validation.order_types.mip_dna.models.sample import MIPDNASample
from cg.services.orders.validation.order_types.tomte.models.sample import TomteSample
from cg.services.orders.validation.rules.case_sample.pedigree.models import FamilyTree, Node


def validate_tree(pedigree: FamilyTree) -> list[PedigreeError]:
    """This performs a DFS algorithm on the family tree to find any cycles, which indicates an
    order error."""
    errors: list[PedigreeError] = []
    for node in pedigree.nodes:
        if not node.visited:
            detect_cycles(node=node, errors=errors)
    return errors


def detect_cycles(node: Node, errors: list[PedigreeError]) -> None:
    """Detect cycles in the pedigree graph using depth-first search. If a cycle is detected,
    this is considered an error."""
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
    """Called when the node's 'mother' creates a cycle in the family tree. For clearer feedback
    we distinguish between the sample being its own mother, and other more complex situations."""
    sample: TomteSample | MIPDNASample | ExistingSample = node.sample
    if node.sample_name == sample.mother:
        return SampleIsOwnMotherError(sample_index=node.sample_index, case_index=node.case_index)
    return DescendantAsMotherError(sample_index=node.sample_index, case_index=node.case_index)


def get_father_error(node: Node) -> PedigreeError:
    """Called when the node's 'father' creates a cycle in the family tree. For clearer feedback
    we distinguish between the sample being its own father, and other more complex situations."""
    sample: TomteSample = node.sample
    if node.sample_name == sample.father:
        return SampleIsOwnFatherError(sample_index=node.sample_index, case_index=node.case_index)
    return DescendantAsFatherError(sample_index=node.sample_index, case_index=node.case_index)
