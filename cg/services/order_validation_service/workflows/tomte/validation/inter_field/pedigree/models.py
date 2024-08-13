from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase
from cg.services.order_validation_service.workflows.tomte.models.sample import (
    TomteSample,
)


class Node:
    def __init__(self, sample: TomteSample, case_index: int, sample_index: int):
        self.sample: TomteSample = sample
        self.sample_index: int = sample_index
        self.case_index: int = case_index
        self.father: Node | None = None
        self.mother: Node | None = None
        self.visited = False
        self.in_current_path = False


class FamilyTree:
    def __init__(self, case: TomteCase, case_index: int):
        self.graph: dict[str, Node] = {}
        self.case: TomteCase = case
        self.case_index: int = case_index
        self._add_nodes()
        self.add_edges()

    def _add_nodes(self) -> None:
        for sample_index, sample in self.case.enumerated_samples:
            node = Node(sample=sample, sample_index=sample_index, case_index=self.case_index)
            self.graph[sample.name] = node

    def add_edges(self) -> None:
        for node in self.graph.values():
            sample: TomteSample = node.sample
            if sample.mother:
                node.mother = self.graph.get(sample.mother)
            if sample.father:
                node.father = self.graph.get(sample.father)

    @property
    def nodes(self) -> list[Node]:
        return list(self.graph.values())
