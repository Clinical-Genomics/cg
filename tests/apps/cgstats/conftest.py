from datetime import datetime
from pathlib import Path
from typing import Dict

import pytest
from pydantic.v1 import BaseModel

from cg.apps.cgstats.crud import create
from cg.apps.cgstats.db.models import Supportparams, Sample, Project, Datasource, Demux
from cg.apps.cgstats.stats import StatsAPI
from cg.models.demultiplex.demux_results import DemuxResults
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData
from tests.models.demultiplexing.conftest import (
    fixture_demultiplexed_dragen_flow_cell,
    fixture_dragen_demux_results,
)


class MockDemuxResults:
    """Mock Demux Results"""

    def __init__(self, flow_cell_full_name: str, sample_sheet_path: Path):
        self.bcl_converter = "dragen"
        self.conversion_stats_path = Path("Demultiplex_Stats.csv")
        self.demux_host = "hasta"
        self.flow_cell: FlowCellDirectoryData = self.mock_flowcell(
            flow_cell_full_name=flow_cell_full_name
        )
        self.machine_name = "barbara"
        self.run_date = datetime.now()
        self.run_name = flow_cell_full_name
        self.results_dir = Path("results_dir/unaligned")
        self.sample_sheet_path = sample_sheet_path
        self.run_info = self.RunInfo()

    class LogfileParameters(BaseModel):
        id_string: str = "id_string"
        program: str = "dragen"
        command_line: str = "command_line"
        time: datetime = datetime.now()

    class RunInfo(BaseModel):
        basemask: str = "151,10,10,151"

    def get_logfile_parameters(self) -> LogfileParameters:
        return self.LogfileParameters()

    @staticmethod
    def mock_flowcell(flow_cell_full_name: str) -> FlowCellDirectoryData:
        return FlowCellDirectoryData(flow_cell_path=Path(flow_cell_full_name))


class MockDemuxSample(BaseModel):
    """Mock Demux Sample"""

    pass_filter_qscore: float = 0.85
    pass_filter_Q30: float = 0.90
    perfect_barcodes: int = 100
    barcodes: int = 10
    raw_clusters_pc: float = 0.0
    pass_filter_clusters: int = 0
    pass_filter_yield_pc: float = 0.0
    pass_filter_yield: int = 0
    lane: int = 1


@pytest.fixture(name="nipt_stats_api")
def fixture_nipt_stats_api(
    stats_api: StatsAPI,
    bcl2fastq_flow_cell_full_name: str,
    novaseq_bcl2fastq_sample_sheet_path: Path,
    sample_id: str,
    ticket_id: str,
):
    nipt_stats_api: StatsAPI = stats_api
    mock_demux_sample = MockDemuxSample(pass_filter_clusters=600000000, pass_filter_Q30=0.90)
    mock_demux_results = MockDemuxResults(
        flow_cell_full_name=bcl2fastq_flow_cell_full_name,
        sample_sheet_path=novaseq_bcl2fastq_sample_sheet_path,
    )

    project_obj: Project = create.create_project(manager=nipt_stats_api, project_name=ticket_id)
    support_parameters_obj: Supportparams = create.create_support_parameters(
        manager=nipt_stats_api, demux_results=mock_demux_results
    )
    flowcell_obj: FlowCellDirectoryData = create.create_flowcell(
        manager=nipt_stats_api, demux_results=mock_demux_results
    )
    datasource_obj: Datasource = create.create_datasource(
        manager=nipt_stats_api,
        demux_results=mock_demux_results,
        support_parameters_id=support_parameters_obj.supportparams_id,
    )
    demux_obj: Demux = create.create_demux(
        manager=nipt_stats_api,
        flow_cell_id=flowcell_obj.flowcell_id,
        datasource_id=datasource_obj.datasource_id,
        demux_results=mock_demux_results,
    )
    sample_obj: Sample = create.create_sample(
        manager=nipt_stats_api,
        sample_id=sample_id,
        barcode="51,8,8,51",
        project_id=project_obj.project_id,
    )
    create.create_unaligned(
        manager=nipt_stats_api,
        demux_id=demux_obj.demux_id,
        demux_sample=mock_demux_sample,
        sample_id=sample_obj.sample_id,
    )
    return nipt_stats_api


@pytest.fixture(name="demultiplexing_stats_path")
def fixture_demultiplexing_stats_path(bcl2fastq_demux_results: DemuxResults) -> Path:
    return bcl2fastq_demux_results.demux_stats_path


@pytest.fixture(name="conversion_stats_path")
def fixture_conversion_stats_path(bcl2fastq_demux_results: DemuxResults) -> Path:
    return bcl2fastq_demux_results.conversion_stats_path


@pytest.fixture(name="run_info_path")
def fixture_run_info(context_config: Dict[str, str]) -> Path:
    return Path(context_config["demultiplex"]["out_dir"]).joinpath(
        "211101_A00187_0615_AHLG5GDRXY/Unaligned/Reports/RunInfo.xml"
    )


@pytest.fixture(name="quality_metrics_path")
def fixture_quality_metrics(context_config: Dict[str, str]) -> Path:
    return Path(context_config["demultiplex"]["out_dir"]).joinpath(
        "211101_A00187_0615_AHLG5GDRXY/Unaligned/Reports/Quality_Metrics.csv"
    )


@pytest.fixture(name="adapter_metrics_path")
def fixture_adapter_metrics(context_config: Dict[str, str]) -> Path:
    return Path(context_config["demultiplex"]["out_dir"]).joinpath(
        "211101_A00187_0615_AHLG5GDRXY/Unaligned/Reports/Adapter_Metrics.csv"
    )
