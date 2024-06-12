"""Tests for the illumina flow cell filters in the store."""

from sqlalchemy.orm import Query

from cg.services.illumina_services.illumina_metrics_service.models import IlluminaFlowCellDTO
from cg.store.filters.status_illumina_flow_cell_filters import (
    filter_illumina_flow_cell_by_internal_id,
)
from cg.store.models import IlluminaFlowCell
from cg.store.store import Store


def test_filter_illumina_flow_cell_by_internal_id(
    illumina_flow_cell_dto: IlluminaFlowCellDTO,
    novaseq_x_flow_cell_id: str,
    store_with_illumina_sequencing_data: Store,
):
    # GIVEN a store with the canonical Illumina flow cells
    flow_cells: Query = store_with_illumina_sequencing_data._get_query(table=IlluminaFlowCell)
    assert flow_cells.count() == 7

    # WHEN filtering an Illumina flow cell by internal id
    flow_cell: Query = filter_illumina_flow_cell_by_internal_id(
        flow_cells=flow_cells, internal_id=novaseq_x_flow_cell_id
    )

    # THEN a query with the correct flow cell should be returned
    assert flow_cell.count() == 1
    assert flow_cell.first().internal_id == novaseq_x_flow_cell_id
