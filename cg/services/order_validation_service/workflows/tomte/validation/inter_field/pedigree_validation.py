from pydantic import BaseModel
from cg.services.order_validation_service.models.errors import (
    PedigreeError,
    SampleHasOffspringAsParent,
    SampleIsOwnParentError,
)
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase
from cg.services.order_validation_service.workflows.tomte.models.sample import TomteSample


class Node:
    def __init__(self, sample: TomteSample, mother: TomteSample | None, father: TomteSample | None):
        self.sample = sample
        self.father = father
        self.mother = mother
        self.visited = False
        self.in_stack = False


class Pedigree:
    def __init__(self, case: TomteCase):
        self.pedigree = {}
        self.case = case

        for sample in case.samples:
            self._add_node(sample)

    def _add_node(self, sample: TomteSample) -> None:
        mother = self.case.get_sample(sample.mother)
        father = self.case.get_sample(sample.father)
        node = Node(sample=sample, mother=mother, father=father)
        self.pedigree[sample.name] = node

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

            if not parent:
                continue

            parent_node: Node = self.pedigree.get(parent.name)
            if parent_node:
                if parent_node.in_stack:
                    if parent_node == node:
                        errors.append(
                            SampleIsOwnParentError(
                                field="error",
                                sample_name=node.sample.name,
                                case_name=self.case.name,
                            )
                        )
                    else:
                        errors.append(
                            SampleHasOffspringAsParent(
                                field="error",
                                sample_name=node.sample.name,
                                case_name=self.case.name,
                            )
                        )
                elif not parent_node.visited:
                    self._dfs(parent_node, errors)

        node.in_stack = False


def get_pedigree_errors(case: TomteCase) -> list[PedigreeError]:
    pedigree = Pedigree(case)
    return pedigree.validate()
