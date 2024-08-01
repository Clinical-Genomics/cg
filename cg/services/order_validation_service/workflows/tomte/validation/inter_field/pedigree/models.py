from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase
from cg.services.order_validation_service.workflows.tomte.models.sample import TomteSample


class Node:
    def __init__(self, sample: TomteSample, case_name: str):
        self.sample = sample
        self.case_name = case_name
        self.father: Node | None = None
        self.mother: Node | None = None
        self.visited = False
        self.in_current_path = False


class FamilyTree:
    def __init__(self, case: TomteCase):
        self.graph: dict[str, Node] = {}
        self.case = case
        self._add_nodes()
        self.add_edges()

    def _add_nodes(self) -> None:
        for sample in self.case.samples:
            node = Node(sample=sample, case_name=self.case.name)
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
        return self.graph.values()
