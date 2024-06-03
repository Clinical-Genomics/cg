"""Module to test the illumina post processing service."""

from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina_services.illumina_post_processing_service.illumina_post_processing_service import (
    IlluminaPostProcessingService,
)
from cg.store.models import IlluminaFlowCell, IlluminaSequencingRun, IlluminaSampleSequencingMetrics


def test_get_illumina_flow_cell(
    novaseq_x_demux_runs_flow_cell: IlluminaRunDirectoryData,
    illumina_post_postprocessing_service: IlluminaPostProcessingService,
):
    # GIVEN a flow cell directory data and an Illumina post processing service

    # WHEN creating an Illumina flow cell
    flow_cell: IlluminaFlowCell = illumina_post_postprocessing_service.store_illumina_flow_cell(
        flow_cell_dir_data=novaseq_x_demux_runs_flow_cell
    )

    # THEN assert that the flow cell is created
    assert isinstance(flow_cell, IlluminaFlowCell)
    assert flow_cell.internal_id == novaseq_x_demux_runs_flow_cell.id


def test_get_illumina_sequencing_run(
    novaseq_x_demux_runs_flow_cell: IlluminaRunDirectoryData,
    illumina_flow_cell: IlluminaFlowCell,
    illumina_post_postprocessing_service: IlluminaPostProcessingService,
):
    # GIVEN a flow cell directory data and an Illumina post processing service

    # WHEN creating an Illumina sequencing run
    sequencing_run: IlluminaSequencingRun = (
        illumina_post_postprocessing_service.store_illumina_sequencing_run(
            flow_cell_dir_data=novaseq_x_demux_runs_flow_cell, flow_cell=illumina_flow_cell
        )
    )

    # THEN assert that the sequencing run is created
    assert isinstance(sequencing_run, IlluminaSequencingRun)


def test_get_illumina_sample_sequencing_metrics(
    novaseq_x_demux_runs_flow_cell: IlluminaRunDirectoryData,
    illumina_post_postprocessing_service: IlluminaPostProcessingService,
):
    # GIVEN a flow cell directory data and an Illumina post processing service
    flow_cell: IlluminaFlowCell = illumina_post_postprocessing_service.store_illumina_flow_cell(
        novaseq_x_demux_runs_flow_cell
    )
    sequencing_run: IlluminaSequencingRun = (
        illumina_post_postprocessing_service.store_illumina_sequencing_run(
            flow_cell_dir_data=novaseq_x_demux_runs_flow_cell, flow_cell=flow_cell
        )
    )

    # WHEN creating Illumina sample sequencing metrics
    sample_metrics: list[IlluminaSampleSequencingMetrics] = (
        illumina_post_postprocessing_service.store_illumina_sample_sequencing_metrics(
            flow_cell_dir_data=novaseq_x_demux_runs_flow_cell,
            sequencing_run=sequencing_run,
        )
    )

    # THEN assert that the sample metrics are created
    assert isinstance(sample_metrics, list)
    assert isinstance(sample_metrics[0], IlluminaSampleSequencingMetrics)


def test_store_illumina_flow_cell_data(
    novaseq_x_demux_runs_flow_cell: IlluminaRunDirectoryData,
    illumina_post_postprocessing_service: IlluminaPostProcessingService,
):
    # GIVEN a flow cell directory data and an Illumina post processing service

    # WHEN storing the flow cell data
    illumina_post_postprocessing_service.store_illumina_flow_cell_data(
        flow_cell_dir_data=novaseq_x_demux_runs_flow_cell
    )

    # THEN assert there is an IlluminaFlowCell in status db
    flow_cell: IlluminaFlowCell = illumina_post_postprocessing_service.status_db._get_query(
        table=IlluminaFlowCell
    ).first()
    assert flow_cell.internal_id == novaseq_x_demux_runs_flow_cell.id

    # THEN assert there is an IlluminaSequencingRun in status db
    sequencing_run: IlluminaSequencingRun = (
        illumina_post_postprocessing_service.status_db._get_query(
            table=IlluminaSequencingRun
        ).first()
    )
    assert sequencing_run

    # THEN illumina sample sequencing metrics are stored in status db
    sample_metrics: list[IlluminaSampleSequencingMetrics] = (
        illumina_post_postprocessing_service.status_db._get_query(
            table=IlluminaSampleSequencingMetrics
        ).all()
    )
    assert sample_metrics

    # THEN the relationship between the flow cell, the sequencing run and sample metrics is correct
    assert sequencing_run.device == flow_cell
    assert sequencing_run.sample_metrics == sample_metrics
    assert flow_cell.instrument_runs == [sequencing_run]
    assert all(sample_metric.instrument_run == sequencing_run for sample_metric in sample_metrics)
