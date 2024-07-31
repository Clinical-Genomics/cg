from cg.services.order_validation_service.models.errors import (
    PedigreeError,
    SampleHasOffspringAsParent,
    SampleIsOwnParentError,
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

        for parent in [node.mother, node.father]:
            if parent is None:
                continue

            if parent.in_stack:
                if parent == node:
                    error = SampleIsOwnParentError(
                        field="error",
                        sample_name=node.sample.name,
                        case_name=self.case.name,
                    )
                else:
                    error = SampleHasOffspringAsParent(
                        field="error",
                        sample_name=node.sample.name,
                        case_name=self.case.name,
                    )
                errors.append(error)
            elif not parent.visited:
                self._dfs(parent, errors)

        node.in_stack = False


def get_pedigree_errors(case: TomteCase) -> list[PedigreeError]:
    pedigree = Pedigree(case)
    return pedigree.validate()
