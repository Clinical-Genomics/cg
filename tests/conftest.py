"""Conftest file for pytest fixtures that needs to be shared for multiple tests."""
import copy
import gzip
import http
import logging
import os
import shutil
from datetime import MAXYEAR, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Generator, List, Tuple, Union

import pytest
from housekeeper.store.models import File, Version
from requests import Response

from cg.apps.cgstats.crud import create
from cg.apps.cgstats.stats import StatsAPI
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.demultiplex.sample_sheet.models import (
    FlowCellSampleNovaSeq6000Bcl2Fastq,
    FlowCellSampleNovaSeq6000Dragen,
)
from cg.apps.gens import GensAPI
from cg.apps.gt import GenotypeAPI
from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims.api import LimsAPI
from cg.constants import FileExtensions, Pipeline
from cg.constants.constants import CaseActions, FileFormat
from cg.constants.demultiplexing import BclConverter, DemultiplexingDirsAndFiles
from cg.constants.priority import SlurmQos
from cg.constants.subject import Gender
from cg.io.controller import ReadFile, WriteFile
from cg.io.json import read_json, write_json
from cg.io.yaml import write_yaml
from cg.meta.rsync import RsyncAPI
from cg.meta.transfer.external_data import ExternalDataAPI
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models import CompressionData
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.demux_results import DemuxResults
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData
from cg.models.demultiplex.run_parameters import RunParametersNovaSeq6000, RunParametersNovaSeqX
from cg.store import Store
from cg.store.models import (
    Bed,
    BedVersion,
    Customer,
    Family,
    Organism,
    Sample,
    SampleLaneSequencingMetrics,
)
from cg.utils import Process
from tests.mocks.crunchy import MockCrunchyAPI
from tests.mocks.hk_mock import MockHousekeeperAPI
from tests.mocks.limsmock import MockLimsAPI
from tests.mocks.madeline import MockMadelineAPI
from tests.mocks.osticket import MockOsTicket
from tests.mocks.process_mock import ProcessMock
from tests.mocks.scout import MockScoutAPI
from tests.mocks.tb_mock import MockTB
from tests.small_helpers import SmallHelpers
from tests.store_helpers import StoreHelpers

LOG = logging.getLogger(__name__)


# Timestamp fixture


@pytest.fixture(name="old_timestamp", scope="session")
def fixture_old_timestamp() -> datetime:
    """Return a time stamp in date time format."""
    return datetime(1900, 1, 1)


@pytest.fixture(name="timestamp", scope="session")
def fixture_timestamp() -> datetime:
    """Return a time stamp in date time format."""
    return datetime(2020, 5, 1)


@pytest.fixture(name="later_timestamp", scope="session")
def fixture_later_timestamp() -> datetime:
    """Return a time stamp in date time format."""
    return datetime(2020, 6, 1)


@pytest.fixture(name="future_date", scope="session")
def fixture_future_date() -> datetime:
    """Return a distant date in the future for which no events happen later."""
    return datetime(MAXYEAR, 1, 1, 1, 1, 1)


@pytest.fixture(name="timestamp_now", scope="session")
def fixture_timestamp_now() -> datetime:
    """Return a time stamp of today's date in date time format."""
    return datetime.now()


@pytest.fixture(name="timestamp_yesterday", scope="session")
def fixture_timestamp_yesterday(timestamp_now: datetime) -> datetime:
    """Return a time stamp of yesterday's date in date time format."""
    return timestamp_now - timedelta(days=1)


@pytest.fixture(name="timestamp_in_2_weeks", scope="session")
def fixture_timestamp_in_2_weeks(timestamp_now: datetime) -> datetime:
    """Return a time stamp 14 days ahead in time."""
    return timestamp_now + timedelta(days=14)


# Case fixtures


@pytest.fixture(name="slurm_account", scope="session")
def fixture_slurm_account() -> str:
    """Return a SLURM account."""
    return "super_account"


@pytest.fixture(name="user_name", scope="session")
def fixture_user_name() -> str:
    """Return a user name."""
    return "Paul Anderson"


@pytest.fixture(name="user_mail", scope="session")
def fixture_user_mail() -> str:
    """Return a user email."""
    return "paul@magnolia.com"


@pytest.fixture(name="email_adress", scope="session")
def fixture_email_adress() -> str:
    """Return an email adress."""
    return "james.holden@scilifelab.se"


@pytest.fixture(name="case_id", scope="session")
def fixture_case_id() -> str:
    """Return a case id."""
    return "yellowhog"


@pytest.fixture(name="case_id_does_not_exist", scope="session")
def fixture_case_id_does_not_exist() -> str:
    """Return a case id that should not exist."""
    return "case_does_not_exist"


@pytest.fixture(name="another_case_id", scope="session")
def fixture_another_case_id() -> str:
    """Return another case id."""
    return "another_case_id"


@pytest.fixture(name="sample_id", scope="session")
def fixture_sample_id() -> str:
    """Return a sample id."""
    return "ADM1"


@pytest.fixture(name="father_sample_id", scope="session")
def fixture_father_sample_id() -> str:
    """Return the sample id of the father."""
    return "ADM2"


@pytest.fixture(name="mother_sample_id", scope="session")
def fixture_mother_sample_id() -> str:
    """Return the mothers sample id."""
    return "ADM3"


@pytest.fixture(name="invalid_sample_id", scope="session")
def fixture_invalid_sample_id() -> str:
    """Return an invalid sample id."""
    return "invalid-sample-id"


@pytest.fixture(name="sample_ids", scope="session")
def fixture_sample_ids(sample_id: str, father_sample_id: str, mother_sample_id: str) -> List[str]:
    """Return a list with three samples of a family."""
    return [sample_id, father_sample_id, mother_sample_id]


@pytest.fixture(name="sample_name", scope="session")
def fixture_sample_name() -> str:
    """Returns a sample name."""
    return "a_sample_name"


@pytest.fixture(name="cust_sample_id", scope="session")
def fixture_cust_sample_id() -> str:
    """Returns a customer sample id."""
    return "child"


@pytest.fixture(name="family_name", scope="session")
def fixture_family_name() -> str:
    """Return a case name."""
    return "case"


@pytest.fixture(name="customer_id", scope="session")
def fixture_customer_id() -> str:
    """Return a customer id."""
    return "cust000"


@pytest.fixture(name="sbatch_job_number", scope="session")
def fixture_sbatch_job_number() -> int:
    return 123456


@pytest.fixture(name="sbatch_process", scope="session")
def fixture_sbatch_process(sbatch_job_number: int) -> ProcessMock:
    """Return a mocked process object."""
    slurm_process = ProcessMock(binary="sbatch")
    slurm_process.set_stdout(text=str(sbatch_job_number))
    return slurm_process


@pytest.fixture(name="analysis_family_single_case")
def fixture_analysis_family_single(
    case_id: str, family_name: str, sample_id: str, ticket_id: str
) -> dict:
    """Build an example case."""
    return {
        "name": family_name,
        "internal_id": case_id,
        "data_analysis": str(Pipeline.MIP_DNA),
        "application_type": "wgs",
        "panels": ["IEM", "EP"],
        "tickets": ticket_id,
        "samples": [
            {
                "name": "proband",
                "sex": Gender.MALE,
                "internal_id": sample_id,
                "status": "affected",
                "original_ticket": ticket_id,
                "reads": 5000000000,
                "capture_kit": "GMSmyeloid",
            }
        ],
    }


@pytest.fixture(name="analysis_family")
def fixture_analysis_family(case_id: str, family_name: str, sample_id: str, ticket_id: str) -> dict:
    """Return a dictionary with information from a analysis case."""
    return {
        "name": family_name,
        "internal_id": case_id,
        "data_analysis": str(Pipeline.MIP_DNA),
        "application_type": "wgs",
        "tickets": ticket_id,
        "panels": ["IEM", "EP"],
        "samples": [
            {
                "name": "child",
                "sex": Gender.MALE,
                "internal_id": sample_id,
                "father": "ADM2",
                "mother": "ADM3",
                "status": "affected",
                "original_ticket": ticket_id,
                "reads": 5000000,
                "capture_kit": "GMSmyeloid",
            },
            {
                "name": "father",
                "sex": Gender.MALE,
                "internal_id": "ADM2",
                "status": "unaffected",
                "original_ticket": ticket_id,
                "reads": 6000000,
                "capture_kit": "GMSmyeloid",
            },
            {
                "name": "mother",
                "sex": Gender.FEMALE,
                "internal_id": "ADM3",
                "status": "unaffected",
                "original_ticket": ticket_id,
                "reads": 7000000,
                "capture_kit": "GMSmyeloid",
            },
        ],
    }


# Config fixtures


@pytest.fixture(name="base_config_dict")
def fixture_base_config_dict() -> dict:
    """Returns the basic configs necessary for running CG."""
    return {
        "database": "sqlite:///",
        "madeline_exe": "path/to/madeline",
        "delivery_path": "path/to/delivery",
        "housekeeper": {
            "database": "sqlite:///",
            "root": "path/to/root",
        },
        "email_base_settings": {
            "sll_port": 465,
            "smtp_server": "smtp.gmail.com",
            "sender_email": "test@gmail.com",
            "sender_password": "",
        },
        "loqusdb": {
            "binary_path": "binary",
            "config_path": "config",
        },
        "loqusdb-wes": {
            "binary_path": "binary_wes",
            "config_path": "config_wes",
        },
        "loqusdb-somatic": {
            "binary_path": "binary_somatic",
            "config_path": "config_somatic",
        },
        "loqusdb-tumor": {
            "binary_path": "binary_tumor",
            "config_path": "config_tumor",
        },
    }


@pytest.fixture(name="cg_config_object")
def fixture_cg_config_object(base_config_dict: dict) -> CGConfig:
    """Return a CG config."""
    return CGConfig(**base_config_dict)


@pytest.fixture(name="chanjo_config")
def fixture_chanjo_config() -> Dict[str, Dict[str, str]]:
    """Return Chanjo config."""
    return {"chanjo": {"config_path": "chanjo_config", "binary_path": "chanjo"}}


@pytest.fixture(name="crunchy_config")
def crunchy_config() -> Dict[str, Dict[str, Any]]:
    """Return Crunchy config."""
    return {
        "crunchy": {
            "conda_binary": "a conda binary",
            "cram_reference": "/path/to/fasta",
            "slurm": {
                "account": "mock_account",
                "conda_env": "mock_env",
                "hours": 1,
                "mail_user": "mock_mail",
                "memory": 1,
                "number_tasks": 1,
            },
        }
    }


@pytest.fixture(name="hk_config_dict")
def fixture_hk_config_dict(root_path: Path):
    """Housekeeper configs."""
    return {
        "housekeeper": {
            "database": "sqlite:///:memory:",
            "root": str(root_path),
        }
    }


@pytest.fixture(name="genotype_config")
def fixture_genotype_config() -> dict:
    """Genotype config fixture."""
    return {
        "genotype": {
            "database": "database",
            "config_path": "config/path",
            "binary_path": "gtdb",
        }
    }


@pytest.fixture(name="gens_config")
def fixture_gens_config() -> Dict[str, Dict[str, str]]:
    """Gens config fixture."""
    return {
        "gens": {
            "config_path": Path("config", "path").as_posix(),
            "binary_path": "gens",
        }
    }


# Api fixtures


@pytest.fixture(name="rsync_api")
def fixture_rsync_api(cg_context: CGConfig) -> RsyncAPI:
    """RsyncAPI fixture."""
    return RsyncAPI(config=cg_context)


@pytest.fixture(name="external_data_api")
def fixture_external_data_api(analysis_store, cg_context: CGConfig) -> ExternalDataAPI:
    """ExternalDataAPI fixture."""
    return ExternalDataAPI(config=cg_context)


@pytest.fixture(name="genotype_api")
def fixture_genotype_api(genotype_config: dict) -> GenotypeAPI:
    """Genotype API fixture."""
    _genotype_api = GenotypeAPI(genotype_config)
    _genotype_api.set_dry_run(True)
    return _genotype_api


@pytest.fixture(name="gens_api")
def fixture_gens_api(gens_config: dict) -> GensAPI:
    """Gens API fixture."""
    _gens_api = GensAPI(gens_config)
    _gens_api.set_dry_run(True)
    return _gens_api


@pytest.fixture()
def madeline_api(madeline_output) -> MockMadelineAPI:
    """madeline_api fixture."""
    _api = MockMadelineAPI()
    _api.set_outpath(madeline_output)
    return _api


@pytest.fixture(name="ticket_id", scope="session")
def fixture_ticket_number() -> str:
    """Return a ticket number for testing."""
    return "123456"


@pytest.fixture(name="osticket")
def fixture_os_ticket(ticket_id: str) -> MockOsTicket:
    """Return a api that mock the os ticket api."""
    api = MockOsTicket()
    api.set_ticket_nr(ticket_id)
    return api


# Files fixtures

# Common file name fixtures


@pytest.fixture(name="snv_vcf_file")
def fixture_snv_vcf_file() -> str:
    """Return a single nucleotide variant file name."""
    return f"snv{FileExtensions.VCF}"


@pytest.fixture(name="sv_vcf_file")
def fixture_sv_vcf_file() -> str:
    """Return a structural variant file name."""
    return f"sv{FileExtensions.VCF}"


@pytest.fixture(name="snv_research_vcf_file")
def fixture_snv_research_vcf_file() -> str:
    #    """Return a single nucleotide variant research file name."""
    return f"snv_research{FileExtensions.VCF}"


@pytest.fixture(name="sv_research_vcf_file")
def fixture_sv_research_vcf_file() -> str:
    """Return a structural variant research file name."""
    return f"sv_research{FileExtensions.VCF}"


# Common file fixtures
@pytest.fixture(scope="session", name="fixtures_dir")
def fixture_fixtures_dir() -> Path:
    """Return the path to the fixtures dir."""
    return Path("tests", "fixtures")


@pytest.fixture(name="analysis_dir", scope="session")
def fixture_analysis_dir(fixtures_dir: Path) -> Path:
    """Return the path to the analysis dir."""
    return Path(fixtures_dir, "analysis")


@pytest.fixture(name="microsalt_analysis_dir", scope="session")
def fixture_microsalt_analysis_dir(analysis_dir: Path) -> Path:
    """Return the path to the analysis dir."""
    return Path(analysis_dir, "microsalt")


@pytest.fixture(name="apps_dir", scope="session")
def fixture_apps_dir(fixtures_dir: Path) -> Path:
    """Return the path to the apps dir."""
    return Path(fixtures_dir, "apps")


@pytest.fixture(name="cgweb_orders_dir", scope="session")
def fixture_cgweb_orders_dir(fixtures_dir: Path) -> Path:
    """Return the path to the cgweb_orders dir."""
    return Path(fixtures_dir, "cgweb_orders")


@pytest.fixture(name="fastq_dir")
def fixture_fastq_dir(demultiplexed_runs: Path) -> Path:
    """Return the path to the fastq files dir."""
    return Path(demultiplexed_runs, "fastq")


@pytest.fixture(name="project_dir")
def fixture_project_dir(tmpdir_factory) -> Generator[Path, None, None]:
    """Path to a temporary directory where intermediate files can be stored."""
    yield Path(tmpdir_factory.mktemp("data"))


@pytest.fixture()
def tmp_file(project_dir) -> Path:
    """Return a temp file path."""
    return Path(project_dir, "test")


@pytest.fixture(name="non_existing_file_path")
def fixture_non_existing_file_path(project_dir: Path) -> Path:
    """Return the path to a non-existing file."""
    return Path(project_dir, "a_file.txt")


@pytest.fixture(name="content", scope="session")
def fixture_content() -> str:
    """Return some content for a file."""
    return (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt"
        " ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ull"
        "amco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehende"
        "rit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaec"
        "at cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
    )


@pytest.fixture(name="filled_file")
def fixture_filled_file(non_existing_file_path: Path, content: str) -> Path:
    """Return the path to a existing file with some content."""
    with open(non_existing_file_path, "w") as outfile:
        outfile.write(content)
    return non_existing_file_path


@pytest.fixture(scope="session", name="orderforms")
def fixture_orderform(fixtures_dir: Path) -> Path:
    """Return the path to the directory with order forms."""
    return Path(fixtures_dir, "orderforms")


@pytest.fixture(name="hk_file")
def fixture_hk_file(filled_file, case_id) -> File:
    """Return a housekeeper File object."""
    return File(id=case_id, path=filled_file)


@pytest.fixture(name="mip_dna_store_files")
def fixture_mip_dna_store_files(apps_dir: Path) -> Path:
    """Return the path to the directory with mip dna store files."""
    return Path(apps_dir, "mip", "dna", "store")


@pytest.fixture(name="case_qc_sample_info_path")
def fixture_case_qc_sample_info_path(mip_dna_store_files: Path) -> Path:
    """Return path to case_qc_sample_info.yaml."""
    return Path(mip_dna_store_files, "case_qc_sample_info.yaml")


@pytest.fixture(name="delivery_report_html")
def fixture_delivery_report_html(mip_dna_store_files: Path) -> Path:
    """Return the path to a qc metrics deliverables file with case data."""
    return Path(mip_dna_store_files, "empty_delivery_report.html")


@pytest.fixture(name="mip_deliverables_file")
def fixture_mip_deliverables_files(mip_dna_store_files: Path) -> Path:
    """Fixture for general deliverables file in mip."""
    return Path(mip_dna_store_files, "case_id_deliverables.yaml")


@pytest.fixture(name="case_qc_metrics_deliverables")
def fixture_case_qc_metrics_deliverables(apps_dir: Path) -> Path:
    """Return the path to a qc metrics deliverables file with case data."""
    return Path(apps_dir, "mip", "case_metrics_deliverables.yaml")


@pytest.fixture(name="mip_analysis_dir")
def fixture_mip_analysis_dir(analysis_dir: Path) -> Path:
    """Return the path to the directory with mip analysis files."""
    return Path(analysis_dir, "mip")


@pytest.fixture(name="balsamic_analysis_dir")
def fixture_balsamic_analysis_dir(analysis_dir: Path) -> Path:
    """Return the path to the directory with balsamic analysis files."""
    return Path(analysis_dir, "balsamic")


@pytest.fixture(name="balsamic_wgs_analysis_dir")
def fixture_balsamic_wgs_analysis_dir(balsamic_analysis_dir: Path) -> Path:
    """Return the path to the directory with balsamic analysis files."""
    return Path(balsamic_analysis_dir, "tn_wgs")


@pytest.fixture(name="mip_dna_analysis_dir")
def fixture_mip_dna_analysis_dir(mip_analysis_dir: Path) -> Path:
    """Return the path to the directory with mip dna analysis files."""
    return Path(mip_analysis_dir, "dna")


@pytest.fixture(name="rnafusion_analysis_dir")
def fixture_rnafusion_analysis_dir(analysis_dir: Path) -> Path:
    """Return the path to the directory with rnafusion analysis files."""
    return Path(analysis_dir, "rnafusion")


@pytest.fixture(name="taxprofiler_analysis_dir")
def fixture_taxprofiler_analysis_dir(analysis_dir: Path) -> Path:
    """Return the path to the directory with taxprofiler analysis files."""
    return Path(analysis_dir, "taxprofiler")


@pytest.fixture(name="sample_cram")
def fixture_sample_cram(mip_dna_analysis_dir: Path) -> Path:
    """Return the path to the cram file for a sample."""
    return Path(mip_dna_analysis_dir, "adm1.cram")


@pytest.fixture(name="father_sample_cram")
def fixture_father_sample_cram(
    mip_dna_analysis_dir: Path,
    father_sample_id: str,
) -> Path:
    """Return the path to the cram file for the father sample."""
    return Path(mip_dna_analysis_dir, father_sample_id + FileExtensions.CRAM)


@pytest.fixture(name="mother_sample_cram")
def fixture_mother_sample_cram(mip_dna_analysis_dir: Path, mother_sample_id: str) -> Path:
    """Return the path to the cram file for the mother sample."""
    return Path(mip_dna_analysis_dir, mother_sample_id + FileExtensions.CRAM)


@pytest.fixture(name="sample_cram_files")
def fixture_sample_crams(
    sample_cram: Path, father_sample_cram: Path, mother_sample_cram: Path
) -> List[Path]:
    """Return a list of cram paths for three samples."""
    return [sample_cram, father_sample_cram, mother_sample_cram]


@pytest.fixture(name="vcf_file")
def fixture_vcf_file(mip_dna_store_files: Path) -> Path:
    """Return the path to a VCF file."""
    return Path(mip_dna_store_files, "yellowhog_clinical_selected.vcf")


@pytest.fixture(name="fastq_file")
def fixture_fastq_file(fastq_dir: Path) -> Path:
    """Return the path to a FASTQ file."""
    return Path(fastq_dir, "dummy_run_R1_001.fastq.gz")


@pytest.fixture(name="madeline_output")
def fixture_madeline_output(apps_dir: Path) -> Path:
    """Return str of path for file with Madeline output."""
    return Path(apps_dir, "madeline", "madeline.xml")


@pytest.fixture(name="file_does_not_exist")
def fixture_file_does_not_exist() -> Path:
    """Return a file path that does not exist."""
    return Path("file", "does", "not", "exist")


# Compression fixtures


@pytest.fixture(name="run_name")
def fixture_run_name() -> str:
    """Return the name of a fastq run."""
    return "fastq_run"


@pytest.fixture(name="original_fastq_data")
def fixture_original_fastq_data(fastq_dir: Path, run_name) -> CompressionData:
    """Return a compression object with a path to the original fastq files."""
    return CompressionData(Path(fastq_dir, run_name))


@pytest.fixture(name="fastq_stub")
def fixture_fastq_stub(project_dir: Path, run_name: str) -> Path:
    """Creates a path to the base format of a fastq run."""
    return Path(project_dir, run_name)


@pytest.fixture(name="compression_object")
def fixture_compression_object(
    fastq_stub: Path, original_fastq_data: CompressionData
) -> CompressionData:
    """Creates compression data object with information about files used in fastq compression."""
    working_files: CompressionData = CompressionData(fastq_stub)
    working_file_map: Dict[str, str] = {
        original_fastq_data.fastq_first.as_posix(): working_files.fastq_first.as_posix(),
        original_fastq_data.fastq_second.as_posix(): working_files.fastq_second.as_posix(),
    }
    for original_file, working_file in working_file_map.items():
        shutil.copy(original_file, working_file)
    return working_files


# Demultiplex fixtures


@pytest.fixture(name="lims_novaseq_dragen_samples")
def fixture_lims_novaseq_dragen_samples(
    lims_novaseq_samples_raw: List[dict],
) -> List[FlowCellSampleNovaSeq6000Dragen]:
    """Return a list of parsed Dragen flow cell samples"""
    return [FlowCellSampleNovaSeq6000Dragen(**sample) for sample in lims_novaseq_samples_raw]


@pytest.fixture(name="lims_novaseq_bcl2fastq_samples")
def fixture_lims_novaseq_bcl2fastq_samples(
    lims_novaseq_samples_raw: List[dict],
) -> List[FlowCellSampleNovaSeq6000Bcl2Fastq]:
    """Return a list of parsed Bcl2fastq flow cell samples"""
    return [FlowCellSampleNovaSeq6000Bcl2Fastq(**sample) for sample in lims_novaseq_samples_raw]


@pytest.fixture(name="stats_api")
def fixture_stats_api(project_dir: Path) -> StatsAPI:
    """Setup base CGStats store."""
    _store = StatsAPI(
        {
            "cgstats": {
                "binary_path": "echo",
                "database": "sqlite://",
                "root": "tests/fixtures/DEMUX",
            }
        }
    )
    _store.create_all()
    yield _store
    _store.drop_all()


@pytest.fixture(name="demux_results_not_finished_dir")
def fixture_demux_results_not_finished_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to a dir with demultiplexing results where demux has been done but nothing is cleaned."""
    return Path(demultiplex_fixtures, "demultiplexed-runs-unfinished")


@pytest.fixture(name="flow_cell_runs_working_directory")
def fixture_flow_cell_runs_working_directory(project_dir: Path) -> Path:
    """Return the path to a working directory with flow cells ready for demux."""
    working_dir: Path = Path(project_dir, "flow-cell-runs", "nova_seq_6000")
    working_dir.mkdir(parents=True)
    return working_dir


@pytest.fixture(name="flow_cell_runs_working_directory_bcl2fastq")
def fixture_flow_cell_runs_working_directory_bcl2fastq(
    flow_cell_runs_working_directory: Path,
) -> Path:
    """Return the path to a working directory with flow cells ready for demux."""
    working_dir: Path = Path(flow_cell_runs_working_directory)
    return working_dir


@pytest.fixture(name="flow_cell_runs_working_directory_dragen")
def fixture_flow_cell_runs_working_directory_dragen(flow_cell_runs_working_directory: Path) -> Path:
    """Return the path to a working directory with flow cells ready for demux."""
    working_dir: Path = Path(flow_cell_runs_working_directory)
    return working_dir


@pytest.fixture(name="demultiplexed_flow_cells_working_directory")
def fixture_demultiplexed_flow_cells_working_directory(project_dir: Path) -> Path:
    """Return the path to a working directory with flow cells that have been demultiplexed."""
    working_dir: Path = Path(project_dir, "demultiplexed-runs")
    working_dir.mkdir(parents=True)
    return working_dir


@pytest.fixture(name="demultiplexed_flow_cell_working_directory")
def fixture_demultiplexed_flow_cell_working_directory(
    demux_results_not_finished_dir: Path,
    demultiplexed_flow_cells_working_directory: Path,
    bcl2fastq_flow_cell_full_name: str,
) -> Path:
    """Copy the content of a demultiplexed but not finished directory to a temporary location."""
    source: Path = Path(demux_results_not_finished_dir, bcl2fastq_flow_cell_full_name)
    destination: Path = Path(
        demultiplexed_flow_cells_working_directory, bcl2fastq_flow_cell_full_name
    )
    shutil.copytree(src=source, dst=destination)
    return destination


@pytest.fixture(name="demultiplexed_flow_cell_finished_working_directory")
def fixture_demultiplexed_flow_cell_finished_working_directory(
    demultiplexed_runs: Path,
    demultiplexed_flow_cells_working_directory: Path,
    bcl2fastq_flow_cell_full_name: str,
) -> Path:
    """Copy the content of a demultiplexed but not finished directory to a temporary location."""
    source: Path = Path(demultiplexed_runs, bcl2fastq_flow_cell_full_name)
    destination: Path = Path(
        demultiplexed_flow_cells_working_directory, bcl2fastq_flow_cell_full_name
    )
    shutil.copytree(src=source, dst=destination)
    return destination


@pytest.fixture(name="flow_cell_working_directory")
def fixture_flow_cell_working_directory(
    bcl2fastq_flow_cell_dir: Path, flow_cell_runs_working_directory: Path
) -> Path:
    """Return the path to a working directory that will be deleted after test is run.

    This is a path to a flow cell directory with the run parameters present.
    """
    working_dir: Path = Path(flow_cell_runs_working_directory, bcl2fastq_flow_cell_dir.name)
    working_dir.mkdir(parents=True)

    existing_flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
        flow_cell_path=bcl2fastq_flow_cell_dir
    )
    working_flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(flow_cell_path=working_dir)
    shutil.copy(
        existing_flow_cell.run_parameters_path.as_posix(),
        working_flow_cell.run_parameters_path.as_posix(),
    )
    return working_dir


@pytest.fixture(name="flow_cell_working_directory_bcl2fastq")
def fixture_flow_cell_working_directory_bcl2fastq(
    bcl2fastq_flow_cell_dir: Path, flow_cell_runs_working_directory_bcl2fastq: Path
) -> Path:
    """Return the path to a working directory that will be deleted after test is run.

    This is a path to a flow cell directory with the run parameters present.
    """
    working_dir: Path = Path(
        flow_cell_runs_working_directory_bcl2fastq, bcl2fastq_flow_cell_dir.name
    )
    working_dir.mkdir(parents=True)
    existing_flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
        flow_cell_path=bcl2fastq_flow_cell_dir
    )
    working_flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(flow_cell_path=working_dir)
    shutil.copy(
        existing_flow_cell.run_parameters_path.as_posix(),
        working_flow_cell.run_parameters_path.as_posix(),
    )
    return working_dir


@pytest.fixture(name="flow_cell_working_directory_dragen")
def fixture_flow_cell_working_directory_dragen(
    dragen_flow_cell_dir: Path, flow_cell_runs_working_directory_dragen: Path
) -> Path:
    """Return the path to a working directory that will be deleted after test is run.

    This is a path to a flow cell directory with the run parameters present.
    """
    working_dir: Path = Path(flow_cell_runs_working_directory_dragen, dragen_flow_cell_dir.name)
    working_dir.mkdir(parents=True)
    existing_flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
        flow_cell_path=dragen_flow_cell_dir
    )
    working_flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(flow_cell_path=working_dir)
    shutil.copy(
        existing_flow_cell.run_parameters_path.as_posix(),
        working_flow_cell.run_parameters_path.as_posix(),
    )
    return working_dir


@pytest.fixture(name="flow_cell_working_directory_no_run_parameters")
def fixture_flow_cell_working_directory_no_run_parameters(
    bcl2fastq_flow_cell_dir: Path, flow_cell_runs_working_directory: Path
) -> Path:
    """This is a path to a flow cell directory with the run parameters missing."""
    working_dir: Path = Path(flow_cell_runs_working_directory, bcl2fastq_flow_cell_dir.name)
    working_dir.mkdir(parents=True)
    return working_dir


@pytest.fixture(name="demultiplex_ready_flow_cell")
def fixture_demultiplex_ready_flow_cell(
    flow_cell_working_directory: Path, bcl2fastq_flow_cell_dir: Path
) -> Path:
    """Return the path to a working directory that is ready for demultiplexing.

    This is a path to a flow cell directory with all the files necessary to start demultiplexing present.
    """
    existing_flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
        flow_cell_path=bcl2fastq_flow_cell_dir
    )
    working_flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
        flow_cell_path=flow_cell_working_directory
    )
    shutil.copy(
        existing_flow_cell.sample_sheet_path.as_posix(),
        working_flow_cell.sample_sheet_path.as_posix(),
    )
    shutil.copy(
        str(DemultiplexingAPI.get_stderr_logfile(existing_flow_cell)),
        str(DemultiplexingAPI.get_stderr_logfile(working_flow_cell)),
    )
    working_flow_cell.copy_complete_path.touch()
    working_flow_cell.rta_complete_path.touch()
    return flow_cell_working_directory


@pytest.fixture(name="demultiplex_ready_flow_cell_bcl2fastq")
def fixture_demultiplex_ready_flow_cell_bcl2fastq(
    flow_cell_working_directory_bcl2fastq: Path, bcl2fastq_flow_cell_dir: Path
) -> Path:
    """Return the path to a working directory that is ready for demultiplexing.

    This is a path to a flow cell directory with all the files necessary to start demultiplexing present.
    """
    existing_flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
        flow_cell_path=bcl2fastq_flow_cell_dir
    )
    working_flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
        flow_cell_path=flow_cell_working_directory_bcl2fastq
    )
    shutil.copy(
        existing_flow_cell.sample_sheet_path.as_posix(),
        working_flow_cell.sample_sheet_path.as_posix(),
    )
    shutil.copy(
        str(DemultiplexingAPI.get_stderr_logfile(existing_flow_cell)),
        str(DemultiplexingAPI.get_stderr_logfile(working_flow_cell)),
    )
    working_flow_cell.copy_complete_path.touch()
    working_flow_cell.rta_complete_path.touch()
    return flow_cell_working_directory_bcl2fastq


@pytest.fixture(name="demultiplex_ready_flow_cell_dragen")
def fixture_demultiplex_ready_flow_cell_dragen(
    flow_cell_working_directory_dragen: Path, dragen_flow_cell_dir: Path
) -> Path:
    """Return the path to a working directory that is ready for demultiplexing.

    This is a path to a flow cell directory with all the files necessary to start demultiplexing present.
    """
    existing_flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
        flow_cell_path=dragen_flow_cell_dir, bcl_converter="dragen"
    )
    working_flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
        flow_cell_path=flow_cell_working_directory_dragen, bcl_converter="dragen"
    )
    shutil.copy(
        existing_flow_cell.sample_sheet_path.as_posix(),
        working_flow_cell.sample_sheet_path.as_posix(),
    )
    shutil.copy(
        str(DemultiplexingAPI.get_stderr_logfile(existing_flow_cell)),
        str(DemultiplexingAPI.get_stderr_logfile(working_flow_cell)),
    )
    working_flow_cell.copy_complete_path.touch()
    working_flow_cell.rta_complete_path.touch()
    return flow_cell_working_directory_dragen


@pytest.fixture(name="sample_sheet_context")
def fixture_sample_sheet_context(cg_context: CGConfig, lims_api: LimsAPI) -> CGConfig:
    """Return cg context with an added lims API."""
    cg_context.lims_api_ = lims_api
    return cg_context


@pytest.fixture(name="bcl_convert_demultiplexed_flow_cell_sample_internal_ids", scope="session")
def fixture_bcl_convert_demultiplexed_flow_cell_sample_internal_ids() -> List[str]:
    """
    Sample id:s present in sample sheet for dummy flow cell demultiplexed with BCL Convert in
    cg/tests/fixtures/apps/demultiplexing/demultiplexed-runs/230504_A00689_0804_BHY7FFDRX2.
    """
    return ["ACC11927A2", "ACC11927A5"]


@pytest.fixture(name="bcl2fastq_demultiplexed_flow_cell_sample_internal_ids", scope="session")
def fixture_bcl2fastq_demultiplexed_flow_cell_sample_internal_ids() -> List[str]:
    """
    Sample id:s present in sample sheet for dummy flow cell demultiplexed with BCL Convert in
    cg/tests/fixtures/apps/demultiplexing/demultiplexed-runs/170407_ST-E00198_0209_BHHKVCALXX.
    """
    return ["SVE2528A1"]


@pytest.fixture(name="flow_cell_name_demultiplexed_with_bcl2fastq", scope="session")
def fixture_flow_cell_name_demultiplexed_with_bcl2fastq() -> str:
    """Return the name of a flow cell that has been demultiplexed with BCL2Fastq."""
    return "HHKVCALXX"


@pytest.fixture(name="flow_cell_directory_name_demultiplexed_with_bcl2fastq", scope="session")
def flow_cell_directory_name_demultiplexed_with_bcl2fastq(
    flow_cell_name_demultiplexed_with_bcl2fastq: str,
):
    """Return the name of a flow cell directory that has been demultiplexed with BCL2Fastq."""
    return f"170407_ST-E00198_0209_B{flow_cell_name_demultiplexed_with_bcl2fastq}"


@pytest.fixture
def store_with_demultiplexed_samples(
    store: Store,
    helpers: StoreHelpers,
    bcl_convert_demultiplexed_flow_cell_sample_internal_ids: List[str],
    bcl2fastq_demultiplexed_flow_cell_sample_internal_ids: List[str],
) -> Store:
    """Return a store with samples that have been demultiplexed with BCL Convert and BCL2Fastq."""
    for i, sample_id in enumerate(bcl_convert_demultiplexed_flow_cell_sample_internal_ids):
        helpers.add_sample(store, internal_id=sample_id, name=f"sample_bcl_convert_{i}")

    for i, sample_id in enumerate(bcl2fastq_demultiplexed_flow_cell_sample_internal_ids):
        helpers.add_sample(store, internal_id=sample_id, name=f"sample_bcl2fastq_{i}")
    return store


@pytest.fixture(name="demultiplex_context")
def fixture_demultiplex_context(
    demultiplexing_api: DemultiplexingAPI,
    stats_api: StatsAPI,
    real_housekeeper_api: HousekeeperAPI,
    cg_context: CGConfig,
    store_with_demultiplexed_samples: Store,
) -> CGConfig:
    """Return cg context with a demultiplex context."""
    cg_context.demultiplex_api_ = demultiplexing_api
    cg_context.cg_stats_api_ = stats_api
    cg_context.housekeeper_api_ = real_housekeeper_api
    cg_context.status_db_ = store_with_demultiplexed_samples
    return cg_context


@pytest.fixture(name="demultiplex_configs")
def fixture_demultiplex_configs(
    flow_cell_runs_working_directory: Path,
    demultiplexed_flow_cells_working_directory: Path,
) -> dict:
    """Return demultiplex configs."""
    demultiplexed_flow_cells_working_directory.mkdir(parents=True, exist_ok=True)
    return {
        "demultiplex": {
            "out_dir": demultiplexed_flow_cells_working_directory.as_posix(),
            "run_dir": flow_cell_runs_working_directory.as_posix(),
            "slurm": {"account": "test", "mail_user": "testuser@github.se"},
        }
    }


@pytest.fixture(name="demultiplexing_api")
def fixture_demultiplexing_api(
    demultiplex_configs: dict, sbatch_process: Process
) -> DemultiplexingAPI:
    """Return demultiplex API."""
    demux_api = DemultiplexingAPI(config=demultiplex_configs)
    demux_api.slurm_api.process = sbatch_process
    return demux_api


@pytest.fixture(name="populated_stats_api")
def fixture_populated_stats_api(
    stats_api: StatsAPI, bcl2fastq_demux_results: DemuxResults
) -> StatsAPI:
    create.create_novaseq_flowcell(manager=stats_api, demux_results=bcl2fastq_demux_results)
    return stats_api


@pytest.fixture(name="novaseq6000_bcl_convert_sample_sheet_path")
def fixture_novaseq6000_sample_sheet_path() -> Path:
    """Return the path to a NovaSeq 6000 BCL convert sample sheet."""
    return Path(
        "tests",
        "fixtures",
        "apps",
        "sequencing_metrics_parser",
        "230622_A00621_0864_AHY7FFDRX2",
        "Unaligned",
        "Reports",
        "SampleSheet.csv",
    )


@pytest.fixture(name="demultiplex_fixtures", scope="session")
def fixture_demultiplex_fixtures(apps_dir: Path) -> Path:
    """Return the path to the demultiplex fixture directory."""
    return Path(apps_dir, "demultiplexing")


@pytest.fixture(name="raw_lims_sample_dir", scope="session")
def fixture_raw_lims_sample_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to the raw samples fixture directory."""
    return Path(demultiplex_fixtures, "raw_lims_samples")


@pytest.fixture(name="run_parameters_dir", scope="session")
def fixture_run_parameters_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to the run parameters fixture directory."""
    return Path(demultiplex_fixtures, "run_parameters")


@pytest.fixture(name="demultiplexed_runs", scope="session")
def fixture_demultiplexed_runs(demultiplex_fixtures: Path) -> Path:
    """Return the path to the demultiplexed flow cells fixture directory."""
    return Path(demultiplex_fixtures, "demultiplexed-runs")


@pytest.fixture(name="flow_cell_runs_dir", scope="session")
def fixture_demux_run_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to the sequenced flow cells fixture directory."""
    return Path(demultiplex_fixtures, "flow-cell-runs")


@pytest.fixture(name="hiseq_dir", scope="session")
def fixture_hiseq_dir(flow_cell_runs_dir: Path) -> Path:
    """Return the path to the hiseq sequencing fixture directory."""
    return Path(flow_cell_runs_dir, "hiseq")


@pytest.fixture(name="novaseq_6000_dir", scope="session")
def fixture_novaseq_6000_dir(flow_cell_runs_dir: Path) -> Path:
    """Return the path to the NovaSeq6000 sequencing fixture directory."""
    return Path(flow_cell_runs_dir, "nova_seq_6000")


@pytest.fixture(name="novaseq_x_dir", scope="session")
def fixture_novaseq_x_dir(flow_cell_runs_dir: Path) -> Path:
    """Return the path to the NovaSeqX sequencing fixture directory."""
    return Path(flow_cell_runs_dir, "nova_seq_x")


@pytest.fixture(name="bcl2fastq_flow_cell_full_name", scope="session")
def fixture_flow_cell_full_name() -> str:
    """Return full flow cell name."""
    return "201203_A00689_0200_AHVKJCDRXX"


@pytest.fixture(name="dragen_flow_cell_full_name", scope="session")
def fixture_dragen_flow_cell_full_name() -> str:
    """Return the full name of a dragen flow cell."""
    return "211101_A00187_0615_AHLG5GDRXY"


@pytest.fixture(name="novaseq_x_flow_cell_full_name", scope="session")
def fixture_novaseq_x_flow_cell_full_name() -> str:
    """Return the full name of a NovaSeqX flow cell."""
    return "20230508_LH00188_0003_A22522YLT3"


@pytest.fixture(name="bcl2fastq_flow_cell_dir", scope="session")
def fixture_bcl2fastq_flow_cell_dir(
    novaseq_6000_dir: Path, bcl2fastq_flow_cell_full_name: str
) -> Path:
    """Return the path to the bcl2fastq flow cell demultiplex fixture directory."""
    return Path(novaseq_6000_dir, bcl2fastq_flow_cell_full_name)


@pytest.fixture(name="dragen_flow_cell_dir", scope="session")
def fixture_dragen_flow_cell_path(novaseq_6000_dir: Path, dragen_flow_cell_full_name: str) -> Path:
    """Return the path to the dragen flow cell demultiplex fixture directory."""
    return Path(novaseq_6000_dir, dragen_flow_cell_full_name)


@pytest.fixture(name="novaseq_x_flow_cell_dir", scope="session")
def fixture_novaseq_x_flow_cell_path(
    novaseq_x_dir: Path, novaseq_x_flow_cell_full_name: str
) -> Path:
    """Return the path to the NovaSeqX flow cell demultiplex fixture directory."""
    return Path(novaseq_x_dir, novaseq_x_flow_cell_full_name)


@pytest.fixture(name="novaseq_bcl2fastq_sample_sheet_path", scope="session")
def fixture_novaseq_bcl2fastq_sample_sheet_path(bcl2fastq_flow_cell_dir: Path) -> Path:
    """Return the path to a NovaSeq6000 Bcl2fastq sample sheet."""
    return Path(bcl2fastq_flow_cell_dir, "SampleSheet.csv")


@pytest.fixture(name="novaseq_dragen_sample_sheet_path", scope="session")
def fixture_novaseq_dragen_sample_sheet_path(dragen_flow_cell_dir: Path) -> Path:
    """Return the path to a NovaSeq6000 dragen sample sheet."""
    return Path(dragen_flow_cell_dir, "SampleSheet.csv")


@pytest.fixture(name="run_parameters_missing_versions_path", scope="session")
def fixture_run_parameters_missing_versions_path(run_parameters_dir: Path) -> Path:
    """Return a NovaSeq6000 run parameters file path without software and reagent kit versions."""
    return Path(run_parameters_dir, "RunParameters_novaseq_no_software_nor_reagent_version.xml")


@pytest.fixture(name="novaseq_6000_run_parameters_path", scope="session")
def fixture_novaseq_6000_run_parameters_path(bcl2fastq_flow_cell_dir: Path) -> Path:
    """Return the path to a file with NovaSeq6000 run parameters."""
    return Path(bcl2fastq_flow_cell_dir, "RunParameters.xml")


@pytest.fixture(name="novaseq_x_run_parameters_path", scope="session")
def fixture_novaseq_x_run_parameters_path(novaseq_x_flow_cell_dir: Path) -> Path:
    """Return the path to a file with NovaSeqX run parameters."""
    return Path(novaseq_x_flow_cell_dir, "RunParameters.xml")


@pytest.fixture(name="run_parameters_novaseq_6000_different_index_path", scope="module")
def fixture_run_parameters_novaseq_6000_different_index_path(run_parameters_dir: Path) -> Path:
    """Return the path to a NovaSeq6000 run parameters file with different index cycles."""
    return Path(run_parameters_dir, "RunParameters_novaseq_6000_different_index_cycles.xml")


@pytest.fixture(name="run_parameters_novaseq_x_different_index_path", scope="module")
def fixture_run_parameters_novaseq_x_different_index_path(run_parameters_dir: Path) -> Path:
    """Return the path to a NovaSeqX run parameters file with different index cycles."""
    return Path(run_parameters_dir, "RunParameters_novaseq_X_different_index_cycles.xml")


@pytest.fixture(name="run_parameters_missing_versions", scope="module")
def fixture_run_parameters_missing_versions(
    run_parameters_missing_versions_path: Path,
) -> RunParametersNovaSeq6000:
    """Return a NovaSeq6000 run parameters object without software and reagent kit versions."""
    return RunParametersNovaSeq6000(run_parameters_path=run_parameters_missing_versions_path)


@pytest.fixture(name="novaseq_6000_run_parameters", scope="session")
def fixture_novaseq_6000_run_parameters(
    novaseq_6000_run_parameters_path: Path,
) -> RunParametersNovaSeq6000:
    """Return a NovaSeq6000 run parameters object."""
    return RunParametersNovaSeq6000(run_parameters_path=novaseq_6000_run_parameters_path)


@pytest.fixture(name="novaseq_x_run_parameters", scope="session")
def fixture_novaseq_x_run_parameters(
    novaseq_x_run_parameters_path: Path,
) -> RunParametersNovaSeqX:
    """Return a NovaSeqX run parameters object."""
    return RunParametersNovaSeqX(run_parameters_path=novaseq_x_run_parameters_path)


@pytest.fixture(name="bcl2fastq_flow_cell", scope="session")
def fixture_flow_cell(bcl2fastq_flow_cell_dir: Path) -> FlowCellDirectoryData:
    """Create a flow cell object with flow cell that is demultiplexed."""
    return FlowCellDirectoryData(
        flow_cell_path=bcl2fastq_flow_cell_dir, bcl_converter=BclConverter.BCL2FASTQ
    )


@pytest.fixture(name="dragen_flow_cell", scope="session")
def fixture_dragen_flow_cell(dragen_flow_cell_dir: Path) -> FlowCellDirectoryData:
    """Create a dragen flow cell object with flow cell that is demultiplexed."""
    return FlowCellDirectoryData(
        flow_cell_path=dragen_flow_cell_dir, bcl_converter=BclConverter.DRAGEN
    )


@pytest.fixture(name="novaseq_x_flow_cell", scope="session")
def fixture_novaseq_x_flow_cell(novaseq_x_flow_cell_dir: Path) -> FlowCellDirectoryData:
    """Create a NovaSeqX flow cell object with flow cell that is demultiplexed."""
    return FlowCellDirectoryData(
        flow_cell_path=novaseq_x_flow_cell_dir, bcl_converter=BclConverter.DRAGEN
    )


@pytest.fixture(name="bcl2fastq_flow_cell_id", scope="session")
def fixture_bcl2fast2_flow_cell_id(bcl2fastq_flow_cell: FlowCellDirectoryData) -> str:
    """Return flow cell id from bcl2fastq flow cell object."""
    return bcl2fastq_flow_cell.id


@pytest.fixture(name="dragen_flow_cell_id", scope="session")
def fixture_dragen_flow_cell_id(dragen_flow_cell: FlowCellDirectoryData) -> str:
    """Return flow cell id from dragen flow cell object."""
    return dragen_flow_cell.id


@pytest.fixture(name="demultiplexing_delivery_file")
def fixture_demultiplexing_delivery_file(bcl2fastq_flow_cell: FlowCellDirectoryData) -> Path:
    """Return demultiplexing delivery started file."""
    return Path(bcl2fastq_flow_cell.path, DemultiplexingDirsAndFiles.DELIVERY)


@pytest.fixture(name="hiseq_x_tile_dir")
def fixture_hiseq_x_tile_dir(bcl2fastq_flow_cell: FlowCellDirectoryData) -> Path:
    """Return Hiseq X tile dir."""
    return Path(bcl2fastq_flow_cell.path, DemultiplexingDirsAndFiles.Hiseq_X_TILE_DIR)


@pytest.fixture(name="lims_novaseq_samples_file")
def fixture_lims_novaseq_samples_file(raw_lims_sample_dir: Path) -> Path:
    """Return the path to a file with sample info in lims format."""
    return Path(raw_lims_sample_dir, "raw_samplesheet_novaseq.json")


@pytest.fixture(name="lims_novaseq_samples_raw")
def fixture_lims_novaseq_samples_raw(lims_novaseq_samples_file: Path) -> List[dict]:
    """Return a list of raw flow cell samples."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=lims_novaseq_samples_file
    )


@pytest.fixture(name="demultiplexed_flow_cell")
def fixture_demultiplexed_flow_cell(
    demultiplexed_runs: Path, bcl2fastq_flow_cell_full_name: str
) -> Path:
    return Path(demultiplexed_runs, bcl2fastq_flow_cell_full_name)


@pytest.fixture(name="bcl2fastq_demux_results")
def fixture_bcl2fastq_demux_results(
    demultiplexed_flow_cell: Path, bcl2fastq_flow_cell: FlowCellDirectoryData
) -> DemuxResults:
    return DemuxResults(
        demux_dir=demultiplexed_flow_cell,
        flow_cell=bcl2fastq_flow_cell,
        bcl_converter=BclConverter.BCL2FASTQ,
    )


# Genotype file fixture


@pytest.fixture(name="bcf_file")
def fixture_bcf_file(apps_dir: Path) -> Path:
    """Return the path to a BCF file."""
    return Path(apps_dir, "gt", "yellowhog.bcf")


# Gens file fixtures


@pytest.fixture(name="gens_fracsnp_path")
def fixture_gens_fracsnp_path(mip_dna_analysis_dir: Path, sample_id: str) -> Path:
    """Path to Gens fracsnp/baf bed file."""
    return Path(mip_dna_analysis_dir, f"{sample_id}.baf.bed.gz")


@pytest.fixture(name="gens_coverage_path")
def fixture_gens_coverage_path(mip_dna_analysis_dir: Path, sample_id: str) -> Path:
    """Path to Gens coverage bed file."""
    return Path(mip_dna_analysis_dir, f"{sample_id}.cov.bed.gz")


# Housekeeper, Chanjo file fixtures


@pytest.fixture(name="bed_file")
def fixture_bed_file(analysis_dir) -> Path:
    """Return the path to a bed file."""
    return Path(analysis_dir, "sample_coverage.bed")


# Helper fixtures


@pytest.fixture(name="helpers", scope="session")
def fixture_helpers() -> StoreHelpers:
    """Return a class with helper functions for the stores."""
    return StoreHelpers()


@pytest.fixture(name="small_helpers")
def fixture_small_helpers() -> SmallHelpers:
    """Return a class with small helper functions."""
    return SmallHelpers()


# HK fixtures


@pytest.fixture(name="root_path")
def fixture_root_path(project_dir: Path) -> Path:
    """Return the path to a hk bundles dir."""
    _root_path = project_dir / "bundles"
    _root_path.mkdir(parents=True, exist_ok=True)
    return _root_path


@pytest.fixture(name="hk_bundle_sample_path")
def fixture_hk_bundle_sample_path(sample_id: str, timestamp: datetime) -> Path:
    """Return the relative path to a HK bundle mock sample."""
    return Path(sample_id, timestamp.strftime("%Y-%m-%d"))


@pytest.fixture(name="hk_bundle_data")
def fixture_hk_bundle_data(case_id: str, bed_file: Path, timestamp: datetime) -> Dict[str, Any]:
    """Return some bundle data for Housekeeper."""
    return {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [{"path": bed_file.as_posix(), "archive": False, "tags": ["bed", "sample"]}],
    }


@pytest.fixture(name="sample_hk_bundle_no_files")
def fixture_sample_hk_bundle_no_files(sample_id: str, timestamp: datetime) -> dict:
    """Create a complete bundle mock for testing compression."""
    return {
        "name": sample_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [],
    }


@pytest.fixture(name="case_hk_bundle_no_files")
def fixture_case_hk_bundle_no_files(case_id: str, timestamp: datetime) -> dict:
    """Create a complete bundle mock for testing compression."""
    return {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [],
    }


@pytest.fixture(name="compress_hk_fastq_bundle")
def fixture_compress_hk_fastq_bundle(
    compression_object: CompressionData, sample_hk_bundle_no_files: dict
) -> dict:
    """Create a complete bundle mock for testing compression

    This bundle contains a pair of fastq files.
    ."""
    hk_bundle_data = copy.deepcopy(sample_hk_bundle_no_files)

    first_fastq = compression_object.fastq_first
    second_fastq = compression_object.fastq_second
    for fastq_file in [first_fastq, second_fastq]:
        fastq_file.touch()
        # We need to set the time to an old date
        # Create a older date
        # Convert the date to a float
        before_timestamp = datetime.timestamp(datetime(2020, 1, 1))
        # Update the utime so file looks old
        os.utime(fastq_file, (before_timestamp, before_timestamp))
        fastq_file_info = {"path": str(fastq_file), "archive": False, "tags": ["fastq"]}

        hk_bundle_data["files"].append(fastq_file_info)
    return hk_bundle_data


@pytest.fixture(name="housekeeper_api")
def fixture_housekeeper_api(hk_config_dict: dict) -> MockHousekeeperAPI:
    """Setup Housekeeper store."""
    return MockHousekeeperAPI(hk_config_dict)


@pytest.fixture(name="real_housekeeper_api")
def fixture_real_housekeeper_api(hk_config_dict: dict) -> Generator[HousekeeperAPI, None, None]:
    """Setup a real Housekeeper store."""
    _api = HousekeeperAPI(hk_config_dict)
    _api.initialise_db()
    yield _api


@pytest.fixture(name="populated_housekeeper_api")
def fixture_populated_housekeeper_api(
    housekeeper_api: MockHousekeeperAPI, hk_bundle_data: dict, helpers
) -> MockHousekeeperAPI:
    """Setup a Housekeeper store with some data."""
    hk_api = housekeeper_api
    helpers.ensure_hk_bundle(hk_api, hk_bundle_data)
    return hk_api


@pytest.fixture(name="hk_version")
def fixture_hk_version(
    housekeeper_api: MockHousekeeperAPI, hk_bundle_data: dict, helpers
) -> Version:
    """Get a Housekeeper version object."""
    return helpers.ensure_hk_version(housekeeper_api, hk_bundle_data)


# Process Mock


@pytest.fixture(name="process")
def fixture_process() -> ProcessMock:
    """Returns a mocked process."""
    return ProcessMock()


# Hermes mock


@pytest.fixture(name="hermes_process")
def fixture_hermes_process() -> ProcessMock:
    """Return a mocked Hermes process."""
    return ProcessMock(binary="hermes")


@pytest.fixture(name="hermes_api")
def fixture_hermes_api(hermes_process: ProcessMock) -> HermesApi:
    """Return a Hermes API with a mocked process."""
    hermes_config = {"hermes": {"binary_path": "/bin/true"}}
    hermes_api = HermesApi(config=hermes_config)
    hermes_api.process = hermes_process
    return hermes_api


# Scout fixtures


@pytest.fixture(name="scout_api")
def fixture_scout_api() -> MockScoutAPI:
    """Setup Scout API."""
    return MockScoutAPI()


# Crunchy fixtures


@pytest.fixture(name="crunchy_api")
def fixture_crunchy_api():
    """Setup Crunchy API."""
    return MockCrunchyAPI()


# Store fixtures


@pytest.fixture(name="analysis_store")
def fixture_analysis_store(
    base_store: Store, analysis_family: dict, wgs_application_tag: str, helpers: StoreHelpers
) -> Generator[Store, None, None]:
    """Setup a store instance for testing analysis API."""
    helpers.ensure_case_from_dict(
        base_store, case_info=analysis_family, app_tag=wgs_application_tag
    )
    yield base_store


@pytest.fixture(name="analysis_store_trio")
def fixture_analysis_store_trio(analysis_store: Store) -> Generator[Store, None, None]:
    """Setup a store instance with a trio loaded for testing analysis API."""
    yield analysis_store


@pytest.fixture(name="analysis_store_single_case")
def fixture_analysis_store_single(
    base_store: Store, analysis_family_single_case: Store, helpers: StoreHelpers
):
    """Setup a store instance with a single ind case for testing analysis API."""
    helpers.ensure_case_from_dict(base_store, case_info=analysis_family_single_case)
    yield base_store


@pytest.fixture(name="collaboration_id")
def fixture_collaboration_id() -> str:
    """Return a default customer group."""
    return "hospital_collaboration"


@pytest.fixture(name="customer_rare_diseases")
def fixture_customer_rare_diseases(collaboration_id: str, customer_id: str) -> Customer:
    """Return a Rare Disease customer."""
    return Customer(
        name="CMMS",
        internal_id="cust003",
        loqus_upload=True,
    )


@pytest.fixture(name="customer_balsamic")
def fixture_customer_balsamic(collaboration_id: str, customer_id: str) -> Customer:
    """Return a Cancer customer."""
    return Customer(
        name="AML",
        internal_id="cust110",
        loqus_upload=True,
    )


@pytest.fixture(name="external_wes_application_tag")
def fixture_external_wes_application_tag() -> str:
    """Return the external whole exome sequencing application tag."""
    return "EXXCUSR000"


@pytest.fixture(name="wgs_application_tag")
def fixture_wgs_application_tag() -> str:
    """Return the WGS application tag."""
    return "WGSPCFC030"


@pytest.fixture(name="store")
def fixture_store() -> Store:
    """Return a CG store."""
    _store = Store(uri="sqlite:///")
    _store.create_all()
    yield _store
    _store.drop_all()


@pytest.fixture(name="apptag_rna")
def fixture_apptag_rna() -> str:
    """Return the RNA application tag."""
    return "RNAPOAR025"


@pytest.fixture(name="bed_name")
def fixture_bed_name() -> str:
    """Return a bed model name attribute."""
    return "Bed"


@pytest.fixture(name="bed_version_file_name")
def fixture_bed_version_filename(bed_name: str) -> str:
    """Return a bed version model file name attribute."""
    return f"{bed_name}.bed"


@pytest.fixture(name="bed_version_short_name")
def fixture_bed_version_short_name() -> str:
    """Return a bed version model short name attribute."""
    return "bed_short_name_0.0"


@pytest.fixture(name="invoice_address")
def fixture_invoice_address() -> str:
    """Return an invoice address."""
    return "Test street"


@pytest.fixture(name="invoice_reference")
def fixture_invoice_reference() -> str:
    """Return an invoice reference."""
    return "ABCDEF"


@pytest.fixture(name="prices")
def fixture_prices() -> Dict[str, int]:
    """Return dictionary with prices for each priority status."""
    return {"standard": 10, "priority": 20, "express": 30, "research": 5}


@pytest.fixture(name="base_store")
def fixture_base_store(
    apptag_rna: str,
    bed_name: str,
    bed_version_short_name: str,
    collaboration_id: str,
    customer_id: str,
    invoice_address: str,
    invoice_reference: str,
    store: Store,
    prices: Dict[str, int],
) -> Store:
    """Setup and example store."""
    collaboration = store.add_collaboration(internal_id=collaboration_id, name=collaboration_id)

    store.session.add(collaboration)
    customers: List[Customer] = []
    customer_map: Dict[str, str] = {
        customer_id: "Production",
        "cust001": "Customer",
        "cust002": "Karolinska",
        "cust003": "CMMS",
    }
    for new_customer_id, new_customer_name in customer_map.items():
        customers.append(
            store.add_customer(
                internal_id=new_customer_id,
                name=new_customer_name,
                scout_access=True,
                invoice_address=invoice_address,
                invoice_reference=invoice_reference,
            )
        )

    for customer in customers:
        collaboration.customers.append(customer)
    store.session.add_all(customers)
    applications = [
        store.add_application(
            tag="WGXCUSC000",
            prep_category="wgs",
            description="External WGS",
            sequencing_depth=0,
            is_external=True,
            percent_kth=80,
            percent_reads_guaranteed=75,
            target_reads=10,
        ),
        store.add_application(
            tag="EXXCUSR000",
            prep_category="wes",
            description="External WES",
            sequencing_depth=0,
            is_external=True,
            percent_kth=80,
            percent_reads_guaranteed=75,
            target_reads=10,
        ),
        store.add_application(
            tag="WGSPCFC060",
            prep_category="wgs",
            description="WGS, double",
            sequencing_depth=30,
            is_accredited=True,
            percent_kth=80,
            percent_reads_guaranteed=75,
            target_reads=10,
        ),
        store.add_application(
            tag="RMLP05R800",
            prep_category="rml",
            description="Ready-made",
            sequencing_depth=0,
            percent_kth=80,
            percent_reads_guaranteed=75,
            target_reads=10,
        ),
        store.add_application(
            tag="WGSPCFC030",
            prep_category="wgs",
            description="WGS trio",
            is_accredited=True,
            sequencing_depth=30,
            target_reads=30,
            limitations="some",
            percent_kth=80,
            percent_reads_guaranteed=75,
            min_sequencing_depth=30,
        ),
        store.add_application(
            tag="METLIFR020",
            prep_category="wgs",
            description="Whole genome metagenomics",
            sequencing_depth=0,
            target_reads=400000,
            percent_kth=80,
            percent_reads_guaranteed=75,
        ),
        store.add_application(
            tag="METNXTR020",
            prep_category="wgs",
            description="Metagenomics",
            sequencing_depth=0,
            target_reads=200000,
            percent_kth=80,
            percent_reads_guaranteed=75,
        ),
        store.add_application(
            tag="MWRNXTR003",
            prep_category="mic",
            description="Microbial whole genome ",
            sequencing_depth=0,
            percent_kth=80,
            percent_reads_guaranteed=75,
            target_reads=10,
        ),
        store.add_application(
            tag=apptag_rna,
            prep_category="tgs",
            description="RNA seq, poly-A based priming",
            percent_kth=80,
            percent_reads_guaranteed=75,
            sequencing_depth=25,
            is_accredited=True,
            target_reads=10,
            min_sequencing_depth=30,
        ),
        store.add_application(
            tag="VWGDPTR001",
            prep_category="cov",
            description="Viral whole genome  ",
            sequencing_depth=0,
            percent_kth=80,
            percent_reads_guaranteed=75,
            target_reads=10,
        ),
    ]

    store.session.add_all(applications)

    versions = [
        store.add_application_version(
            application=application, version=1, valid_from=datetime.now(), prices=prices
        )
        for application in applications
    ]
    store.session.add_all(versions)

    beds: List[Bed] = [store.add_bed(name=bed_name)]
    store.session.add_all(beds)
    bed_versions: List[BedVersion] = [
        store.add_bed_version(
            bed=bed,
            version=1,
            filename=bed_name + FileExtensions.BED,
            shortname=bed_version_short_name,
        )
        for bed in beds
    ]
    store.session.add_all(bed_versions)

    organism = store.add_organism("C. jejuni", "C. jejuni")
    store.session.add(organism)
    store.session.commit()

    yield store


@pytest.fixture()
def sample_store(base_store: Store) -> Store:
    """Populate store with samples."""
    new_samples = [
        base_store.add_sample(name="ordered", sex=Gender.MALE, internal_id="test_internal_id"),
        base_store.add_sample(name="received", sex=Gender.UNKNOWN, received=datetime.now()),
        base_store.add_sample(
            name="received-prepared",
            sex=Gender.UNKNOWN,
            received=datetime.now(),
            prepared_at=datetime.now(),
        ),
        base_store.add_sample(name="external", sex=Gender.FEMALE),
        base_store.add_sample(name="external-received", sex=Gender.FEMALE, received=datetime.now()),
        base_store.add_sample(
            name="sequenced",
            sex=Gender.MALE,
            received=datetime.now(),
            prepared_at=datetime.now(),
            sequenced_at=datetime.now(),
            reads=(310 * 1000000),
        ),
        base_store.add_sample(
            name="sequenced-partly",
            sex=Gender.MALE,
            received=datetime.now(),
            prepared_at=datetime.now(),
            reads=(250 * 1000000),
        ),
        base_store.add_sample(
            name="to-deliver",
            sex=Gender.MALE,
            sequenced_at=datetime.now(),
        ),
        base_store.add_sample(
            name="delivered",
            sex=Gender.MALE,
            sequenced_at=datetime.now(),
            delivered_at=datetime.now(),
            no_invoice=False,
        ),
    ]
    customer: Customer = (base_store.get_customers())[0]
    external_app = base_store.get_application_by_tag("WGXCUSC000").versions[0]
    wgs_app = base_store.get_application_by_tag("WGSPCFC030").versions[0]
    for sample in new_samples:
        sample.customer = customer
        sample.application_version = external_app if "external" in sample.name else wgs_app
    base_store.session.add_all(new_samples)
    base_store.session.commit()
    return base_store


@pytest.fixture(name="trailblazer_api", scope="session")
def fixture_trailblazer_api() -> MockTB:
    """Return a mock Trailblazer API."""
    return MockTB()


@pytest.fixture(name="lims_api", scope="session")
def fixture_lims_api() -> MockLimsAPI:
    """Return a mock LIMS API."""
    return MockLimsAPI()


@pytest.fixture(name="config_root_dir", scope="session")
def fixture_config_root_dir() -> Path:
    """Return a path to the config root directory."""
    return Path("tests", "fixtures", "data")


@pytest.fixture(name="housekeeper_dir", scope="session")
def fixture_housekeeper_dir(tmpdir_factory):
    """Return a temporary directory for Housekeeper testing."""
    return tmpdir_factory.mktemp("housekeeper")


@pytest.fixture(name="mip_dir", scope="session")
def fixture_mip_dir(tmpdir_factory) -> Path:
    """Return a temporary directory for MIP testing."""
    return tmpdir_factory.mktemp("mip")


@pytest.fixture(name="fluffy_dir", scope="session")
def fixture_fluffy_dir(tmpdir_factory) -> Path:
    """Return a temporary directory for Fluffy testing."""
    return tmpdir_factory.mktemp("fluffy")


@pytest.fixture(name="balsamic_dir", scope="session")
def fixture_balsamic_dir(tmpdir_factory) -> Path:
    """Return a temporary directory for Balsamic testing."""
    return tmpdir_factory.mktemp("balsamic")


@pytest.fixture(name="rnafusion_dir", scope="session")
def fixture_rnafusion_dir(tmpdir_factory) -> Path:
    return tmpdir_factory.mktemp("rnafusion")


@pytest.fixture(name="taxprofiler_dir", scope="session")
def fixture_taxprofiler_dir(tmpdir_factory) -> Path:
    return tmpdir_factory.mktemp("taxprofiler")


@pytest.fixture(name="cg_dir", scope="session")
def fixture_cg_dir(tmpdir_factory) -> Path:
    """Return a temporary directory for cg testing."""
    return tmpdir_factory.mktemp("cg")


@pytest.fixture(name="swegen_dir")
def fixture_swegen_dir(tmpdir_factory, tmp_path) -> Path:
    """SweGen temporary directory containing mocked reference files."""
    return tmpdir_factory.mktemp("swegen")


@pytest.fixture(name="swegen_snv_reference")
def fixture_swegen_snv_reference_path(swegen_dir: Path) -> Path:
    """Return a temporary path to a SweGen SNV reference file."""
    mock_file = Path(swegen_dir, "grch37_swegen_10k_snv_-20220101-.vcf.gz")
    mock_file.touch(exist_ok=True)
    return mock_file


@pytest.fixture(name="observations_dir")
def fixture_observations_dir(tmpdir_factory, tmp_path) -> Path:
    """Loqusdb temporary directory containing observations mock files."""
    return tmpdir_factory.mktemp("loqusdb")


@pytest.fixture(name="observations_clinical_snv_file_path")
def fixture_observations_clinical_snv_file_path(observations_dir: Path) -> Path:
    """Return a temporary path to a clinical SNV file."""
    mock_file = Path(observations_dir, "loqusdb_clinical_snv_export-20220101-.vcf.gz")
    mock_file.touch(exist_ok=True)
    return mock_file


@pytest.fixture(name="observations_clinical_sv_file_path")
def fixture_observations_clinical_sv_file_path(observations_dir: Path) -> Path:
    """Return a temporary path to a clinical SV file."""
    mock_file = Path(observations_dir, "loqusdb_clinical_sv_export-20220101-.vcf.gz")
    mock_file.touch(exist_ok=True)
    return mock_file


@pytest.fixture(name="observations_somatic_snv_file_path")
def fixture_observations_somatic_snv_file_path(observations_dir: Path) -> Path:
    """Return a temporary path to a cancer somatic SNV file."""
    mock_file = Path(observations_dir, "loqusdb_cancer_somatic_snv_export-20220101-.vcf.gz")
    mock_file.touch(exist_ok=True)
    return mock_file


@pytest.fixture(name="outdated_observations_somatic_snv_file_path")
def fixture_outdated_observations_somatic_snv_file_path(observations_dir: Path) -> Path:
    """Return a temporary path to an outdated cancer somatic SNV file."""
    mock_file = Path(observations_dir, "loqusdb_cancer_somatic_snv_export-20180101-.vcf.gz")
    mock_file.touch(exist_ok=True)
    return mock_file


@pytest.fixture(name="custom_observations_clinical_snv_file_path")
def fixture_custom_observations_clinical_snv_file_path(observations_dir: Path) -> Path:
    """Return a custom path for the clinical SNV observations file."""
    return Path(observations_dir, "clinical_snv_export-19990101-.vcf.gz")


@pytest.fixture(name="microsalt_dir", scope="session")
def fixture_microsalt_dir(tmpdir_factory) -> Path:
    """Return a temporary directory for Microsalt testing."""
    return tmpdir_factory.mktemp("microsalt")


@pytest.fixture()
def current_encryption_dir() -> Path:
    """Return a temporary directory for current encryption testing."""
    return Path("home", "ENCRYPT")


@pytest.fixture()
def legacy_encryption_dir() -> Path:
    """Return a temporary directory for current encryption testing."""
    return Path("home", "TO_PDC")


@pytest.fixture(name="cg_uri")
def fixture_cg_uri() -> str:
    """Return a cg URI."""
    return "sqlite:///"


@pytest.fixture(name="hk_uri")
def fixture_hk_uri() -> str:
    """Return a Housekeeper URI."""
    return "sqlite:///"


@pytest.fixture(name="loqusdb_id")
def fixture_loqusdb_id() -> str:
    """Returns a Loqusdb mock ID."""
    return "01ab23cd"


@pytest.fixture(name="context_config")
def fixture_context_config(
    cg_uri: str,
    hk_uri: str,
    fluffy_dir: Path,
    housekeeper_dir: Path,
    mip_dir: Path,
    cg_dir: Path,
    balsamic_dir: Path,
    microsalt_dir: Path,
    rnafusion_dir: Path,
    taxprofiler_dir: Path,
) -> dict:
    """Return a context config."""
    return {
        "database": cg_uri,
        "delivery_path": str(cg_dir),
        "email_base_settings": {
            "sll_port": 465,
            "smtp_server": "smtp.gmail.com",
            "sender_email": "test@gmail.com",
            "sender_password": "",
        },
        "madeline_exe": "echo",
        "pon_path": str(cg_dir),
        "backup": {
            "encrypt_dir": {
                "current": str(current_encryption_dir),
                "legacy": str(legacy_encryption_dir),
            },
            "root": {"hiseqx": "flowcells/hiseqx", "hiseqga": "RUNS/", "novaseq": "runs/"},
        },
        "balsamic": {
            "balsamic_cache": "hello",
            "bed_path": str(cg_dir),
            "binary_path": "echo",
            "conda_env": "S_Balsamic",
            "loqusdb_path": str(cg_dir),
            "pon_path": str(cg_dir),
            "root": str(balsamic_dir),
            "slurm": {
                "mail_user": "test.email@scilifelab.se",
                "account": "development",
                "qos": SlurmQos.LOW,
            },
            "swegen_path": str(cg_dir),
        },
        "cgstats": {"binary_path": "echo", "database": "sqlite:///./cgstats", "root": str(cg_dir)},
        "chanjo": {"binary_path": "echo", "config_path": "chanjo-stage.yaml"},
        "crunchy": {
            "conda_binary": "a_conda_binary",
            "cram_reference": "grch37_homo_sapiens_-d5-.fasta",
            "slurm": {
                "account": "development",
                "conda_env": "S_crunchy",
                "hours": 1,
                "mail_user": "an@scilifelab.se",
                "memory": 1,
                "number_tasks": 1,
            },
        },
        "data-delivery": {
            "account": "development",
            "base_path": "/another/path",
            "covid_destination_path": "server.name.se:/another/%s/foldername/",
            "covid_report_path": "/folder_structure/%s/yet_another_folder/filename_%s_data_*.csv",
            "destination_path": "server.name.se:/some",
            "mail_user": "an@email.com",
        },
        "demultiplex": {
            "run_dir": "tests/fixtures/apps/demultiplexing/flow-cell-runs/nova_seq_6000",
            "out_dir": "tests/fixtures/apps/demultiplexing/demultiplexed-runs",
            "slurm": {
                "account": "development",
                "mail_user": "an@scilifelab.se",
            },
        },
        "encryption": {"binary_path": "bin/gpg"},
        "external": {
            "caesar": "server.name.se:/path/%s/on/caesar",
            "hasta": "/path/on/hasta/%s",
        },
        "fluffy": {
            "binary_path": "echo",
            "config_path": "fluffy/Config.json",
            "root_dir": str(fluffy_dir),
            "sftp": {
                "user": "sftpuser",
                "password": "sftpassword",
                "host": "sftphost",
                "remote_path": "sftpremotepath",
                "port": 22,
            },
        },
        "genotype": {
            "binary_path": "echo",
            "config_path": "genotype-stage.yaml",
        },
        "gisaid": {
            "binary_path": "/path/to/gisaid_uploader.py",
            "log_dir": "/path/to/log",
            "logwatch_email": "some@email.com",
            "upload_cid": "cid",
            "upload_password": "pass",
            "submitter": "s.submitter",
        },
        "hermes": {"binary_path": "hermes"},
        "housekeeper": {"database": hk_uri, "root": str(housekeeper_dir)},
        "lims": {
            "host": "https://lims.scilifelab.se",
            "password": "password",
            "username": "user",
        },
        "loqusdb": {"binary_path": "loqusdb", "config_path": "loqusdb-stage.yaml"},
        "loqusdb-wes": {"binary_path": "loqusdb", "config_path": "loqusdb-wes-stage.yaml"},
        "loqusdb-somatic": {"binary_path": "loqusdb", "config_path": "loqusdb-somatic-stage.yaml"},
        "loqusdb-tumor": {"binary_path": "loqusdb", "config_path": "loqusdb-tumor-stage.yaml"},
        "microsalt": {
            "binary_path": "echo",
            "conda_binary": "a_conda_binary",
            "conda_env": "S_microSALT",
            "queries_path": Path(microsalt_dir, "queries").as_posix(),
            "root": str(microsalt_dir),
        },
        "mip-rd-dna": {
            "conda_binary": "a_conda_binary",
            "conda_env": "S_mip9.0",
            "mip_config": "mip9.0-dna-stage.yaml",
            "pipeline": "analyse rd_dna",
            "root": str(mip_dir),
            "script": "mip",
        },
        "mip-rd-rna": {
            "conda_binary": "a_conda_binary",
            "conda_env": "S_mip9.0",
            "mip_config": "mip9.0-rna-stage.yaml",
            "pipeline": "analyse rd_rna",
            "root": str(mip_dir),
            "script": "mip",
        },
        "mutacc-auto": {
            "binary_path": "echo",
            "config_path": "mutacc-auto-stage.yaml",
            "padding": 300,
        },
        "mutant": {
            "binary_path": "echo",
            "conda_binary": "a_conda_binary",
            "conda_env": "S_mutant",
            "root": str(mip_dir),
        },
        "rnafusion": {
            "binary_path": Path("path", "to", "bin", "nextflow").as_posix(),
            "compute_env": "nf_tower_compute_env",
            "conda_binary": Path("path", "to", "bin", "conda").as_posix(),
            "conda_env": "S_RNAFUSION",
            "launch_directory": Path("path", "to", "launchdir").as_posix(),
            "pipeline_path": Path("pipeline", "path").as_posix(),
            "profile": "myprofile",
            "references": Path("path", "to", "references").as_posix(),
            "revision": "2.2.0",
            "root": str(rnafusion_dir),
            "slurm": {
                "account": "development",
                "mail_user": "test.email@scilifelab.se",
            },
            "tower_binary_path": Path("path", "to", "bin", "tw").as_posix(),
            "tower_pipeline": "rnafusion",
        },
        "pdc": {"binary_path": "/bin/dsmc"},
        "taxprofiler": {
            "binary_path": Path("path", "to", "bin", "nextflow").as_posix(),
            "root": str(taxprofiler_dir),
        },
        "scout": {
            "binary_path": "echo",
            "config_path": "scout-stage.yaml",
        },
        "statina": {
            "api_url": "api_url",
            "auth_path": "auth_path",
            "host": "http://localhost:28002",
            "key": "key",
            "upload_path": "upload_path",
            "user": "user",
        },
        "tar": {"binary_path": "/bin/tar"},
        "trailblazer": {
            "host": "https://trailblazer.scilifelab.se/",
            "service_account": "SERVICE",
            "service_account_auth_file": "trailblazer-auth.json",
        },
    }


@pytest.fixture(name="cg_context")
def fixture_cg_context(
    context_config: dict, base_store: Store, housekeeper_api: MockHousekeeperAPI
) -> CGConfig:
    """Return a cg config."""
    cg_config = CGConfig(**context_config)
    cg_config.status_db_ = base_store
    cg_config.housekeeper_api_ = housekeeper_api
    return cg_config


@pytest.fixture(name="case_id_with_single_sample", scope="session")
def fixture_case_id_with_single_sample():
    """Return a case id that should only be associated with one sample."""
    return "exhaustedcrocodile"


@pytest.fixture(name="case_id_with_multiple_samples", scope="session")
def fixture_case_id_with_multiple_samples():
    """Return a case id that should be associated with multiple samples."""
    return "righteouspanda"


@pytest.fixture(name="case_id_without_samples", scope="session")
def fixture_case_id_without_samples():
    """Return a case id that should not be associated with any samples."""
    return "confusedtrout"


@pytest.fixture(name="sample_id_in_single_case", scope="session")
def fixture_sample_id_in_single_case():
    """Return a sample id that should be associated with a single case."""
    return "ASM1"


@pytest.fixture(name="sample_id_in_multiple_cases", scope="session")
def fixture_sample_id_in_multiple_cases():
    """Return a sample id that should be associated with multiple cases."""
    return "ASM2"


@pytest.fixture(name="store_with_multiple_cases_and_samples")
def fixture_store_with_multiple_cases_and_samples(
    case_id_without_samples: str,
    case_id_with_single_sample: str,
    case_id_with_multiple_samples: str,
    sample_id_in_single_case: str,
    sample_id_in_multiple_cases: str,
    case_id: str,
    ticket_id: str,
    helpers: StoreHelpers,
    store: Store,
):
    """Return a store containing multiple cases and samples."""

    helpers.add_case(
        store=store, internal_id=case_id_without_samples, ticket=ticket_id, action="running"
    )
    helpers.add_case_with_samples(
        base_store=store, case_id=case_id_with_multiple_samples, nr_samples=5
    )

    case_samples: List[Tuple[str, str]] = [
        (case_id_with_multiple_samples, sample_id_in_multiple_cases),
        (case_id, sample_id_in_multiple_cases),
        (case_id_with_single_sample, sample_id_in_single_case),
    ]

    for case_sample in case_samples:
        case_id, sample_id = case_sample
        helpers.add_case_with_sample(base_store=store, case_id=case_id, sample_id=sample_id)

    yield store


@pytest.fixture(name="store_with_panels")
def fixture_store_with_panels(store: Store, helpers: StoreHelpers):
    helpers.ensure_panel(store=store, panel_abbreviation="panel1", customer_id="cust000")
    helpers.ensure_panel(store=store, panel_abbreviation="panel2", customer_id="cust000")
    helpers.ensure_panel(store=store, panel_abbreviation="panel3", customer_id="cust000")
    yield store


@pytest.fixture(name="store_with_organisms")
def fixture_store_with_organisms(store: Store, helpers: StoreHelpers) -> Store:
    """Return a store with multiple organisms."""

    organism_details = [
        ("organism_1", "Organism 1"),
        ("organism_2", "Organism 2"),
        ("organism_3", "Organism 3"),
    ]

    organisms: List[Organism] = []
    for internal_id, name in organism_details:
        organism: Organism = helpers.add_organism(store, internal_id=internal_id, name=name)
        organisms.append(organism)

    store.session.add_all(organisms)
    store.session.commit()
    yield store


@pytest.fixture(name="ok_response")
def fixture_ok_response() -> Response:
    """Return a response with the OK status code."""
    response: Response = Response()
    response.status_code = http.HTTPStatus.OK
    return response


@pytest.fixture(name="unauthorized_response")
def fixture_unauthorized_response() -> Response:
    """Return a response with the UNAUTHORIZED status code."""
    response: Response = Response()
    response.status_code = http.HTTPStatus.UNAUTHORIZED
    return response


@pytest.fixture(name="non_existent_email")
def fixture_non_existent_email():
    """Return email not associated with any entity."""
    return "non_existent_email@example.com"


@pytest.fixture(name="non_existent_id")
def fixture_non_existent_id():
    """Return id not associated with any entity."""
    return "non_existent_entity_id"


@pytest.fixture(name="store_with_users")
def fixture_store_with_users(store: Store, helpers: StoreHelpers) -> Store:
    """Return a store with multiple users."""

    customer: Customer = helpers.ensure_customer(store=store)

    user_details = [
        ("user1@example.com", "User One", False),
        ("user2@example.com", "User Two", True),
        ("user3@example.com", "User Three", False),
    ]

    for email, name, is_admin in user_details:
        store.add_user(customer=customer, email=email, name=name, is_admin=is_admin)

    store.session.commit()

    yield store


@pytest.fixture(name="store_with_cases_and_customers")
def fixture_store_with_cases_and_customers(store: Store, helpers: StoreHelpers) -> Store:
    """Return a store with cases and customers."""

    customer_details: List[Tuple[str, str, bool]] = [
        ("cust000", "Customer 1", True),
        ("cust001", "Customer 2", False),
        ("cust002", "Customer 3", True),
    ]
    customers = []

    for customer_id, customer_name, scout_access in customer_details:
        customer: Customer = helpers.ensure_customer(
            store=store,
            customer_id=customer_id,
            customer_name=customer_name,
            scout_access=scout_access,
        )
        customers.append(customer)

    case_details: List[Tuple[str, str, Pipeline, CaseActions, Customer]] = [
        ("case 1", "flyingwhale", Pipeline.BALSAMIC, CaseActions.RUNNING, customers[0]),
        ("case 2", "swimmingtiger", Pipeline.FLUFFY, CaseActions.ANALYZE, customers[0]),
        ("case 3", "sadbaboon", Pipeline.SARS_COV_2, CaseActions.HOLD, customers[1]),
        ("case 4", "funkysloth", Pipeline.MIP_DNA, CaseActions.ANALYZE, customers[1]),
        ("case 5", "deadparrot", Pipeline.MICROSALT, CaseActions.RUNNING, customers[2]),
        ("case 6", "anxiousbeetle", Pipeline.DEMULTIPLEX, CaseActions.RUNNING, customers[2]),
    ]

    for case_name, case_id, pipeline, action, customer in case_details:
        helpers.ensure_case(
            store=store,
            case_name=case_name,
            case_id=case_id,
            data_analysis=pipeline.value,
            action=action.value,
            customer=customer,
        )
    store.session.commit()
    yield store


# Rnafusion fixtures


@pytest.fixture(name="rnafusion_dir")
def fixture_rnafusion_dir(tmpdir_factory, apps_dir: Path) -> str:
    """Return the path to the rnafusion apps dir."""
    rnafusion_dir = tmpdir_factory.mktemp("rnafusion")
    return Path(rnafusion_dir).absolute().as_posix()


@pytest.fixture(name="rnafusion_case_id")
def fixture_rnafusion_case_id() -> str:
    """Returns a rnafusion case id."""
    return "rnafusion_case_enough_reads"


@pytest.fixture(name="no_sample_case_id")
def fixture_no_sample_case_id() -> str:
    """Returns a case id of a case with no samples."""
    return "no_sample_case"


@pytest.fixture(name="rnafusion_sample_id")
def fixture_rnafusion_sample_id() -> str:
    """Returns a rnafusion sample id."""
    return "sample_rnafusion_case_enough_reads"


@pytest.fixture(name="rnafusion_housekeeper_dir")
def fixture_rnafusion_housekeeper_dir(tmpdir_factory, rnafusion_dir: Path) -> Path:
    """Return the path to the rnafusion housekeeper bundle dir."""
    return tmpdir_factory.mktemp("bundles")


@pytest.fixture(name="rnafusion_fastq_file_l_1_r_1")
def fixture_rnafusion_fastq_file_l_1_r_1(rnafusion_housekeeper_dir: Path) -> str:
    fastq_filename = Path(
        rnafusion_housekeeper_dir, "XXXXXXXXX_000000_S000_L001_R1_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:1:1101:4806:1047 1:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture(name="rnafusion_fastq_file_l_1_r_2")
def fixture_rnafusion_fastq_file_l_1_r_2(rnafusion_housekeeper_dir: Path) -> str:
    fastq_filename = Path(
        rnafusion_housekeeper_dir, "XXXXXXXXX_000000_S000_L001_R2_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:1:1101:4806:1047 2:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture(name="rnafusion_mock_fastq_files")
def fixture_rnafusion_mock_fastq_files(
    rnafusion_fastq_file_l_1_r_1: Path, rnafusion_fastq_file_l_1_r_2: Path
) -> List[Path]:
    """Return list of all mock fastq files to commit to mock housekeeper"""
    return [rnafusion_fastq_file_l_1_r_1, rnafusion_fastq_file_l_1_r_2]


@pytest.fixture(scope="function", name="rnafusion_housekeeper")
def fixture_rnafusion_housekeeper(
    housekeeper_api: HousekeeperAPI,
    helpers: StoreHelpers,
    rnafusion_mock_fastq_files: List[Path],
    rnafusion_sample_id: str,
):
    """Create populated housekeeper that holds files for all mock samples."""

    bundle_data = {
        "name": rnafusion_sample_id,
        "created": datetime.now(),
        "version": "1.0",
        "files": [
            {"path": f, "tags": ["fastq"], "archive": False} for f in rnafusion_mock_fastq_files
        ],
    }
    helpers.ensure_hk_bundle(store=housekeeper_api, bundle_data=bundle_data)
    return housekeeper_api


@pytest.fixture(scope="function", name="rnafusion_context")
def fixture_rnafusion_context(
    cg_context: CGConfig,
    helpers: StoreHelpers,
    rnafusion_housekeeper: HousekeeperAPI,
    trailblazer_api: MockTB,
    hermes_api: HermesApi,
    cg_dir: Path,
    rnafusion_case_id: str,
    rnafusion_sample_id: str,
    no_sample_case_id: str,
) -> CGConfig:
    """context to use in cli"""
    cg_context.housekeeper_api_ = rnafusion_housekeeper
    cg_context.trailblazer_api_ = trailblazer_api
    cg_context.meta_apis["analysis_api"] = RnafusionAnalysisAPI(config=cg_context)
    status_db: Store = cg_context.status_db

    # Create ERROR case with NO SAMPLES
    helpers.add_case(status_db, internal_id=no_sample_case_id, name=no_sample_case_id)

    # Create textbook case with enough reads
    case_enough_reads: Family = helpers.add_case(
        store=status_db,
        internal_id=rnafusion_case_id,
        name=rnafusion_case_id,
        data_analysis=Pipeline.RNAFUSION,
    )

    sample_rnafusion_case_enough_reads: Sample = helpers.add_sample(
        status_db,
        internal_id=rnafusion_sample_id,
        sequenced_at=datetime.now(),
    )

    helpers.add_relationship(
        status_db,
        case=case_enough_reads,
        sample=sample_rnafusion_case_enough_reads,
    )
    return cg_context


@pytest.fixture(name="deliverable_data")
def fixture_deliverables_data(
    rnafusion_dir: Path, rnafusion_case_id: str, rnafusion_sample_id: str
) -> dict:
    return {
        "files": [
            {
                "path": f"{rnafusion_dir}/{rnafusion_case_id}/multiqc/multiqc_report.html",
                "path_index": "",
                "step": "report",
                "tag": ["multiqc-html", "rna"],
                "id": rnafusion_case_id,
                "format": "html",
                "mandatory": True,
            },
        ]
    }


@pytest.fixture
def mock_deliverable(rnafusion_dir: Path, deliverable_data: dict, rnafusion_case_id: str) -> None:
    """Create deliverable file with dummy data and files to deliver."""
    Path.mkdir(
        Path(rnafusion_dir, rnafusion_case_id),
        parents=True,
        exist_ok=True,
    )
    Path.mkdir(
        Path(rnafusion_dir, rnafusion_case_id, "multiqc"),
        parents=True,
        exist_ok=True,
    )
    for report_entry in deliverable_data["files"]:
        Path(report_entry["path"]).touch(exist_ok=True)
    WriteFile.write_file_from_content(
        content=deliverable_data,
        file_format=FileFormat.JSON,
        file_path=Path(rnafusion_dir, rnafusion_case_id, rnafusion_case_id + "_deliverables.yaml"),
    )


@pytest.fixture(name="hermes_deliverables")
def fixture_hermes_deliverables(deliverable_data: dict, rnafusion_case_id: str) -> dict:
    hermes_output: dict = {"pipeline": "rnafusion", "bundle_id": rnafusion_case_id, "files": []}
    for file_info in deliverable_data["files"]:
        tags: List[str] = []
        if "html" in file_info["format"]:
            tags.append("multiqc-html")
        hermes_output["files"].append({"path": file_info["path"], "tags": tags, "mandatory": True})
    return hermes_output


@pytest.fixture(name="malformed_hermes_deliverables")
def fixture_malformed_hermes_deliverables(hermes_deliverables: dict) -> dict:
    malformed_deliverable: dict = hermes_deliverables.copy()
    malformed_deliverable.pop("pipeline")

    return malformed_deliverable


@pytest.fixture(name="rnafusion_multiqc_json_metrics")
def fixture_rnafusion_multiqc_json_metrics(rnafusion_analysis_dir) -> dict:
    """Returns the content of a mock Multiqc JSON file."""
    return read_json(file_path=Path(rnafusion_analysis_dir, "multiqc_data.json"))


@pytest.fixture(name="tower_id")
def fixture_tower_id() -> int:
    """Returns a NF-Tower ID."""
    return 123456


@pytest.fixture
def mock_analysis_finish(
    rnafusion_dir: Path, rnafusion_case_id: str, rnafusion_multiqc_json_metrics: dict, tower_id: int
) -> None:
    """Create analysis_finish file for testing."""
    Path.mkdir(Path(rnafusion_dir, rnafusion_case_id, "pipeline_info"), parents=True, exist_ok=True)
    Path(rnafusion_dir, rnafusion_case_id, "pipeline_info", "software_versions.yml").touch(
        exist_ok=True
    )
    Path(rnafusion_dir, rnafusion_case_id, f"{rnafusion_case_id}_samplesheet.csv").touch(
        exist_ok=True
    )
    Path.mkdir(
        Path(rnafusion_dir, rnafusion_case_id, "multiqc", "multiqc_data"),
        parents=True,
        exist_ok=True,
    )
    write_json(
        content=rnafusion_multiqc_json_metrics,
        file_path=Path(
            rnafusion_dir,
            rnafusion_case_id,
            "multiqc",
            "multiqc_data",
            "multiqc_data",
        ).with_suffix(FileExtensions.JSON),
    )
    write_yaml(
        content={rnafusion_case_id: [tower_id]},
        file_path=Path(
            rnafusion_dir,
            rnafusion_case_id,
            "tower_ids",
        ).with_suffix(FileExtensions.YAML),
    )


@pytest.fixture
def mock_config(rnafusion_dir: Path, rnafusion_case_id: str) -> None:
    """Create samplesheet.csv file for testing"""
    Path.mkdir(Path(rnafusion_dir, rnafusion_case_id), parents=True, exist_ok=True)
    Path(rnafusion_dir, rnafusion_case_id, f"{rnafusion_case_id}_samplesheet.csv").touch(
        exist_ok=True
    )


@pytest.fixture
def expected_total_reads() -> int:
    return 1_000_000


@pytest.fixture(name="flow_cell_name")
def fixture_flow_cell_name() -> str:
    """Return flow cell name."""
    return "HVKJCDRXX"


@pytest.fixture
def store_with_sequencing_metrics(
    store: Store, sample_id: str, expected_total_reads: int, flow_cell_name: str
) -> Generator[Store, None, None]:
    """Return a store with multiple samples with sample lane sequencing metrics."""

    sample_sequencing_metrics_details: List[Union[str, str, int, int, float, int]] = [
        (sample_id, flow_cell_name, 1, expected_total_reads / 2, 90.5, 32),
        (sample_id, flow_cell_name, 2, expected_total_reads / 2, 90.4, 31),
        ("sample_2", "flow_cell_2", 2, 2_000_000, 85.5, 30),
        ("sample_3", "flow_cell_3", 3, 1_500_000, 80.5, 33),
    ]

    sample_lane_sequencing_metrics: List[SampleLaneSequencingMetrics] = []
    for (
        sample_internal_id,
        flow_cell_name,
        flow_cell_lane_number,
        sample_total_reads_in_lane,
        sample_base_fraction_passing_q30,
        sample_base_mean_quality_score,
    ) in sample_sequencing_metrics_details:
        sequencing_metrics = SampleLaneSequencingMetrics(
            sample_internal_id=sample_internal_id,
            flow_cell_name=flow_cell_name,
            flow_cell_lane_number=flow_cell_lane_number,
            sample_total_reads_in_lane=sample_total_reads_in_lane,
            sample_base_fraction_passing_q30=sample_base_fraction_passing_q30,
            sample_base_mean_quality_score=sample_base_mean_quality_score,
            created_at=datetime.now(),
        )
        sample_lane_sequencing_metrics.append(sequencing_metrics)

    store.session.add_all(sample_lane_sequencing_metrics)
    store.session.commit()
    yield store


@pytest.fixture
def flow_cell_name_demultiplexed_with_bcl_convert() -> str:
    return "HY7FFDRX2"


@pytest.fixture
def flow_cell_directory_name_demultiplexed_with_bcl_convert(
    flow_cell_name_demultiplexed_with_bcl_convert: str,
):
    return f"230504_A00689_0804_B{flow_cell_name_demultiplexed_with_bcl_convert}"


@pytest.fixture(name="demultiplexed_flow_cells_tmp_directory")
def fixture_demultiplexed_flow_cells_tmp_directory(tmp_path) -> Path:
    original_dir = Path(
        Path(__file__).parent, "fixtures", "apps", "demultiplexing", "demultiplexed-runs"
    )
    tmp_dir = Path(tmp_path, "tmp_run_dir")

    return Path(shutil.copytree(original_dir, tmp_dir))
