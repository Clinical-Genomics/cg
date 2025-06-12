from cg.services.orders.validation.models.case_aliases import CaseContainingRelatives
from cg.services.orders.validation.models.existing_sample import ExistingSample
from cg.services.orders.validation.order_types.mip_dna.models.sample import MIPDNASample
from cg.services.orders.validation.order_types.tomte.models.sample import TomteSample
from cg.store.store import Store

SampleWithParents = TomteSample | MIPDNASample | ExistingSample


class Node:
    """
    This class is used to represent the samples in the family tree graph. The variables 'mother' and
    'father' refer to other nodes in the family tree, and can be thought of as an edge in the graph.
    Because the 'mother' and 'father' are tracked using the sample's _name_ in the order, and
    because said name is not set in the ExistingSample model, we require the sample name as a
    separate input.
    """

    def __init__(
        self,
        sample: SampleWithParents,
        case_index: int,
        sample_index: int,
        sample_name: str,
    ):
        self.sample: SampleWithParents = sample
        self.sample_name: str = sample_name
        self.sample_index: int = sample_index
        self.case_index: int = case_index
        self.father: Node | None = None
        self.mother: Node | None = None
        self.visited = False
        self.in_current_path = False


class FamilyTree:
    """
    This class is a directed graph representing a family tree from a submitted order with specified
    mothers and fathers. Each node represents a sample, and each node has a property 'mother' and
    a property 'father' referring to other nodes in the graph. These may be thought of as the
    graph's edges.
    """

    def __init__(self, case: CaseContainingRelatives, case_index: int, store: Store):
        self.graph: dict[str, Node] = {}
        self.case: CaseContainingRelatives = case
        self.case_index: int = case_index
        self.store = store
        self._add_nodes()
        self._add_edges()

    def _add_nodes(self) -> None:
        """Add a node to the graph for each sample in the graph. For existing samples, the name
        is fetched from StatusDB."""
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
        """Add edges to the graph by populating each node's 'mother' and 'father' property."""
        for node in self.graph.values():
            sample: SampleWithParents = node.sample
            if sample.mother:
                node.mother = self.graph.get(sample.mother)
            if sample.father:
                node.father = self.graph.get(sample.father)

    @property
    def nodes(self) -> list[Node]:
        return list(self.graph.values())
