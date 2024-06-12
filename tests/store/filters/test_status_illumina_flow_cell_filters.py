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
    illumina_flow_cell_internal_id: str,
    store: Store,
):
    # GIVEN an Illumina flow cell in store
    store.add_illumina_flow_cell(illumina_flow_cell_dto)

    # WHEN filtering an Illumina flow cell by internal id
    flow_cells: Query = store._get_query(table=IlluminaFlowCell)
    flow_cell: Query = filter_illumina_flow_cell_by_internal_id(
        flow_cells=flow_cells, internal_id=illumina_flow_cell_internal_id
    )

    # THEN a query with the correct flow cell should be returned
    assert isinstance(flow_cell, Query)
    assert flow_cell.first().internal_id == illumina_flow_cell_internal_id
