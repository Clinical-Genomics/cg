from datetime import datetime
from pathlib import Path

import pytest
from pydantic import BaseModel

from cg.apps.cgstats.crud import create
from cg.apps.cgstats.db import models as stats_models
from cg.apps.cgstats.stats import StatsAPI
from cg.models.demultiplex.demux_results import DemuxResults
from cg.models.demultiplex.flowcell import Flowcell
from tests.models.demultiplexing.conftest import (
    fixture_bcl2fastq_demux_results,
    fixture_demultiplexed_dragen_flow_cell,
    fixture_demultiplexed_flowcell,
    fixture_demultiplexed_runs,
    fixture_dragen_demux_results,
    fixture_dragen_flow_cell_full_name,
    fixture_dragen_flow_cell_object,
    fixture_dragen_flow_cell_path,
    fixture_flowcell_object,
    fixture_flowcell_path,
    fixture_flowcell_runs,
)


class MockDemuxResults:
    """Mock Demux Results"""

    def __init__(self, flowcell_full_name: str, sample_sheet_path: Path):
        self.bcl_converter = "dragen"
        self.conversion_stats_path = Path("Demultiplex_Stats.csv")
        self.demux_host = "hasta"
        self.flowcell: Flowcell = self.mock_flowcell(flowcell_full_name=flowcell_full_name)
        self.machine_name = "barbara"
        self.run_date = datetime.now()
        self.run_name = flowcell_full_name
        self.results_dir = Path("results_dir/unaligned")
        self.sample_sheet_path = sample_sheet_path
        self.run_info = self.RunInfo()

    class LogfileParameters(BaseModel):
        id_string: str = "id_string"
        program: str = "dragen"
        command_line: str = "command_line"
        time: datetime = datetime.now()

    class RunInfo(BaseModel):
        index_length: int = 10
        read_length: int = 151

    def get_logfile_parameters(self) -> LogfileParameters:
        return self.LogfileParameters()

    @staticmethod
    def mock_flowcell(flowcell_full_name: str) -> Flowcell:
        return Flowcell(flowcell_path=Path(flowcell_full_name))


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


@pytest.fixture(name="stats_api")
def fixture_stats_api(project_dir: Path) -> StatsAPI:
    """Setup base CGStats store."""
    _store = StatsAPI({"cgstats": {"database": "sqlite://", "root": "tests/fixtures/DEMUX"}})
    _store.create_all()
    yield _store
    _store.drop_all()


@pytest.fixture(name="nipt_stats_api")
def fixture_nipt_stats_api(
    stats_api: StatsAPI,
    flowcell_full_name: str,
    novaseq_dragen_sample_sheet_path: Path,
    sample_id: str,
    ticket_number: int,
):
    nipt_stats_api: StatsAPI = stats_api
    mock_demux_sample = MockDemuxSample(pass_filter_clusters=600000000, pass_filter_Q30=0.90)
    mock_demux_results = MockDemuxResults(
        flowcell_full_name=flowcell_full_name, sample_sheet_path=novaseq_dragen_sample_sheet_path
    )

    project_obj: stats_models.Project = create.create_project(
        manager=nipt_stats_api, project_name=str(ticket_number)
    )
    support_parameters_obj: stats_models.Supportparams = create.create_support_parameters(
        manager=nipt_stats_api, demux_results=mock_demux_results
    )
    flowcell_obj: stats_models.Flowcell = create.create_flowcell(
        manager=nipt_stats_api, demux_results=mock_demux_results
    )
    datasource_obj: stats_models.Datasource = create.create_datasource(
        manager=nipt_stats_api,
        demux_results=mock_demux_results,
        support_parameters_id=support_parameters_obj.supportparams_id,
    )
    demux_obj: stats_models.Demux = create.create_demux(
        manager=nipt_stats_api,
        flowcell_id=flowcell_obj.flowcell_id,
        datasource_id=datasource_obj.datasource_id,
        demux_results=mock_demux_results,
    )
    sample_obj: stats_models.Sample = create.create_sample(
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


@pytest.fixture(name="populated_stats_api")
def fixture_populated_stats_api(
    stats_api: StatsAPI, bcl2fastq_demux_results: DemuxResults
) -> StatsAPI:
    create.create_novaseq_flowcell(manager=stats_api, demux_results=bcl2fastq_demux_results)
    return stats_api


@pytest.fixture(name="demultiplexing_stats_path")
def fixture_demultiplexing_stats_path(bcl2fastq_demux_results: DemuxResults) -> Path:
    return bcl2fastq_demux_results.demux_stats_path


@pytest.fixture(name="conversion_stats_path")
def fixture_conversion_stats_path(bcl2fastq_demux_results: DemuxResults) -> Path:
    return bcl2fastq_demux_results.conversion_stats_path
