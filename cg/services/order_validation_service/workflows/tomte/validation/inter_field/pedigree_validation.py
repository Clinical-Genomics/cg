from cg.services.order_validation_service.models.errors import (
    DescendantAsFatherError,
    PedigreeError,
    DescendantAsMotherError,
    SampleIsOwnFatherError,
    SampleIsOwnMotherError,
)
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase
from cg.services.order_validation_service.workflows.tomte.models.sample import TomteSample


class Node:
    def __init__(self, sample: TomteSample):
        self.sample = sample
        self.father: Node | None = None
        self.mother: Node | None = None
        self.visited = False
        self.in_stack = False


class Pedigree:
    def __init__(self, case: TomteCase):
        self.pedigree: dict[str, Node] = {}
        self.case = case
        self._add_nodes()
        self._add_parents()

    def _add_nodes(self) -> None:
        for sample in self.case.samples:
            node = Node(sample=sample)
            self.pedigree[sample.name] = node

    def _add_parents(self) -> None:
        for node in self.pedigree.values():
            sample: TomteSample = node.sample
            if sample.mother:
                node.mother = self.pedigree.get(sample.mother)
            if sample.father:
                node.father = self.pedigree.get(sample.father)

    def validate(self) -> list[PedigreeError]:
        errors = []
        for node in self.pedigree.values():
            if not node.visited:
                self._dfs(node, errors)
        return errors

    def _dfs(self, node: Node, errors: list[PedigreeError]) -> None:
        node.visited = True
        node.in_stack = True

        parents = {"mother": node.mother, "father": node.father}

        for parent_type, parent in parents.items():
            if parent and parent.in_stack:
                error = get_error(node=node, parent_type=parent_type)
                errors.append(error)
            elif parent and not parent.visited:
                self._dfs(parent, errors)

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


def get_pedigree_errors(case: TomteCase) -> list[PedigreeError]:
    pedigree = Pedigree(case)
    return pedigree.validate()
