from cg.services.order_validation_service.models.errors import (
    DescendantAsFatherError,
    DescendantAsMotherError,
    PedigreeError,
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
        self.in_current_path = False


class Pedigree:
    def __init__(self, case: TomteCase):
        self.graph: dict[str, Node] = {}
        self.case = case
        self._add_nodes()
        self.add_edges()

    def _add_nodes(self) -> None:
        for sample in self.case.samples:
            node = Node(sample=sample)
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

    def validate(self) -> list[PedigreeError]:
        errors = []
        for node in self.nodes:
            if not node.visited:
                self._detect_cycles(node, errors)
        return errors

    def _detect_cycles(self, node: Node, errors: list[PedigreeError]) -> None:
        """Detect cycles in the pedigree graph using depth-first search"""
        node.visited = True
        node.in_current_path = True

        parents = {"mother": node.mother, "father": node.father}

        for parent_type, parent in parents.items():
            if parent and parent.in_current_path:
                error = self._get_error(node=node, parent_type=parent_type)
                errors.append(error)
            elif parent and not parent.visited:
                self._detect_cycles(parent, errors)

        node.in_current_path = False

    def _get_error(self, node: Node, parent_type: str) -> PedigreeError:
        if parent_type == "mother":
            return self._get_mother_error(node)
        if parent_type == "father":
            return self._get_father_error(node)

    def _get_mother_error(self, node: Node) -> PedigreeError:
        sample = node.sample
        if sample.name == sample.mother:
            return SampleIsOwnMotherError(sample_name=sample.name, case_name=self.case.name)
        return DescendantAsMotherError(sample_name=sample.name, case_name=self.case.name)

    def _get_father_error(self, node: Node) -> PedigreeError:
        sample = node.sample
        if sample.name == sample.father:
            return SampleIsOwnFatherError(sample_name=sample.name, case_name=self.case.name)
        return DescendantAsFatherError(sample_name=sample.name, case_name=self.case.name)
