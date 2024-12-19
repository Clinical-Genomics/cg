from cg.services.order_validation_service.models.existing_sample import ExistingSample
from cg.services.order_validation_service.workflows.mip_dna.models.case import MipDnaCase
from cg.services.order_validation_service.workflows.mip_dna.models.sample import MipDnaSample
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase
from cg.services.order_validation_service.workflows.tomte.models.sample import TomteSample
from cg.store.store import Store


class Node:
    def __init__(
        self,
        sample: TomteSample | MipDnaSample | ExistingSample,
        case_index: int,
        sample_index: int,
        sample_name: str,
    ):
        self.sample: TomteSample | MipDnaSample | ExistingSample = sample
        self.sample_name: str = sample_name
        self.sample_index: int = sample_index
        self.case_index: int = case_index
        self.father: Node | None = None
        self.mother: Node | None = None
        self.visited = False
        self.in_current_path = False


class FamilyTree:
    def __init__(self, case: TomteCase | MipDnaCase, case_index: int, store: Store):
        self.graph: dict[str, Node] = {}
        self.case: TomteCase = case
        self.case_index: int = case_index
        self.store = store
        self._add_nodes()
        self._add_edges()

    def _add_nodes(self) -> None:
        for sample_index, sample in self.case.enumerated_samples:
            if sample.is_new:
                sample_name = sample.name
            else:
                sample_name = self.store.get_sample_by_internal_id(sample.internal_id).name
            node = Node(
                sample=sample,
                sample_index=sample_index,
                case_index=self.case_index,
                sample_name=sample_name,
            )
            self.graph[sample_name] = node

    def _add_edges(self) -> None:
        for node in self.graph.values():
            sample: TomteSample = node.sample
            if sample.mother:
                node.mother = self.graph.get(sample.mother)
            if sample.father:
                node.father = self.graph.get(sample.father)

    @property
    def nodes(self) -> list[Node]:
        return list(self.graph.values())
