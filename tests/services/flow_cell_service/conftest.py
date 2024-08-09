import pytest

from cg.services.flow_cell_service.flow_cell_service import FlowCellService
from cg.store.store import Store


@pytest.fixture
def flow_cell_service(store_with_illumina_sequencing_data: Store):
    return FlowCellService(store_with_illumina_sequencing_data)
