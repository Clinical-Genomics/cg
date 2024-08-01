from cg.services.order_validation_service.models.errors import (
    DescendantAsFatherError,
    PedigreeError,
    DescendantAsMotherError,
    SampleIsOwnFatherError,
    SampleIsOwnMotherError,
)
from cg.services.order_validation_service.workflows.tomte.validation.inter_field.pedigree.models import (
    Node,
)


def detect_cycles(node: Node, errors: list[PedigreeError]) -> None:
    node.visited = True
    node.in_stack = True

    parents = {"mother": node.mother, "father": node.father}

    for parent_type, parent in parents.items():
        if parent and parent.in_stack:
            error = get_error(node=node, parent_type=parent_type)
            errors.append(error)
        elif parent and not parent.visited:
            detect_cycles(parent, errors)

    node.in_stack = False


def get_error(node: Node, parent_type: str) -> PedigreeError:
    if parent_type == "mother":
        return get_mother_error(node)
    if parent_type == "father":
        return get_father_error(node)


def get_mother_error(node: Node):
    sample = node.sample
    if sample.name == sample.mother:
        return SampleIsOwnMotherError(sample_name=sample.name, case_name="case_name")
    return DescendantAsMotherError(sample_name=sample.name, case_name="case_name")


def get_father_error(node: Node):
    sample = node.sample
    if sample.name == sample.father:
        return SampleIsOwnFatherError(sample_name=sample.name, case_name="case_name")
    return DescendantAsFatherError(sample_name=sample.name, case_name="case_name")
