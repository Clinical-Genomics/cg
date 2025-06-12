"""Tests for the illumina flow cell filters in the store."""

from sqlalchemy.orm import Query

from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina.data_transfer.models import IlluminaFlowCellDTO
from cg.store.filters.status_illumina_flow_cell_filters import (
    filter_illumina_flow_cell_by_internal_id,
)
from cg.store.models import IlluminaFlowCell
from cg.store.store import Store


def test_filter_illumina_flow_cell_by_internal_id(
    illumina_flow_cell_dto: IlluminaFlowCellDTO,
    novaseq_x_flow_cell_id: str,
    store_with_illumina_sequencing_data: Store,
    seven_canonical_flow_cells: list[IlluminaRunDirectoryData],
):
    # GIVEN a store with the canonical Illumina flow cells
    flow_cells: Query = store_with_illumina_sequencing_data._get_query(table=IlluminaFlowCell)
    number_of_flow_cells_in_store: int = len(seven_canonical_flow_cells)
    assert flow_cells.count() == number_of_flow_cells_in_store

    # WHEN filtering an Illumina flow cell by internal id
    filtered_flow_cells: Query = filter_illumina_flow_cell_by_internal_id(
        flow_cells=flow_cells, internal_id=novaseq_x_flow_cell_id
    )

    # THEN a query with the correct flow cell should be returned
    assert filtered_flow_cells.count() < number_of_flow_cells_in_store
    assert filtered_flow_cells.first().internal_id == novaseq_x_flow_cell_id
