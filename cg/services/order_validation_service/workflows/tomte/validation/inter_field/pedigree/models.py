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
        self.graph: dict[str, Node] = {}
        self.case = case
        self._add_nodes()
        self._add_parents()

    def _add_nodes(self) -> None:
        for sample in self.case.samples:
            node = Node(sample=sample)
            self.graph[sample.name] = node

    def _add_parents(self) -> None:
        for node in self.graph.values():
            sample: TomteSample = node.sample
            if sample.mother:
                node.mother = self.graph.get(sample.mother)
            if sample.father:
                node.father = self.graph.get(sample.father)

    @property
    def nodes(self) -> list[Node]:
        return self.graph.values()
