"""Conftest file for pytest fixtures that needs to be shared for multiple tests."""
import copy

import datetime as dt
import logging
import os
import shutil
from pathlib import Path
from typing import Generator, Dict, List, Any

import pytest
from housekeeper.store.models import File

from cg.apps.gt import GenotypeAPI
from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Pipeline
from cg.constants.constants import FileFormat
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.priority import SlurmQos
from cg.io.controller import ReadFile
from cg.constants.subject import Gender
from cg.meta.rsync import RsyncAPI
from cg.meta.transfer.external_data import ExternalDataAPI
from cg.models import CompressionData
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flow_cell import FlowCell
from cg.store import Store

from .mocks.crunchy import MockCrunchyAPI
from .mocks.hk_mock import MockHousekeeperAPI
from .mocks.limsmock import MockLimsAPI
from .mocks.madeline import MockMadelineAPI
from .mocks.osticket import MockOsTicket
from .mocks.process_mock import ProcessMock
from .mocks.scout import MockScoutAPI
from .mocks.tb_mock import MockTB
from .small_helpers import SmallHelpers
from .store_helpers import StoreHelpers

from housekeeper.store import models as hk_models

LOG = logging.getLogger(__name__)


# Timestamp fixture


@pytest.fixture(scope="function", name="old_timestamp")
def fixture_old_timestamp() -> dt.datetime:
    """Return a time stamp in date time format."""
    return dt.datetime(1900, 1, 1)


@pytest.fixture(scope="function", name="timestamp")
def fixture_timestamp() -> dt.datetime:
    """Return a time stamp in date time format."""
    return dt.datetime(2020, 5, 1)


@pytest.fixture(scope="function", name="later_timestamp")
def fixture_later_timestamp() -> dt.datetime:
    """Return a time stamp in date time format."""
    return dt.datetime(2020, 6, 1)


@pytest.fixture(scope="function", name="timestamp_now")
def fixture_timestamp_now() -> dt.datetime:
    """Return a time stamp of today's date in date time format."""
    return dt.datetime.now()


@pytest.fixture(scope="function", name="timestamp_yesterday")
def fixture_timestamp_yesterday(timestamp_now: dt.datetime) -> dt.datetime:
    """Return a time stamp of yesterday's date in date time format."""
    return timestamp_now - dt.timedelta(days=1)


@pytest.fixture(scope="function", name="timestamp_in_2_weeks")
def fixture_timestamp_in_2_weeks(timestamp_now: dt.datetime) -> dt.datetime:
    """Return a time stamp 14 days ahead in time."""
    return timestamp_now + dt.timedelta(days=14)


# Case fixtures


@pytest.fixture(name="slurm_account")
def fixture_slurm_account() -> str:
    """Return a SLURM account."""
    return "super_account"


@pytest.fixture(name="user_name")
def fixture_user_name() -> str:
    """Return a user name."""
    return "Paul Anderson"


@pytest.fixture(name="user_mail")
def fixture_user_mail() -> str:
    """Return a user email."""
    return "paul@magnolia.com"


@pytest.fixture(name="email_adress")
def fixture_email_adress() -> str:
    """Return an email adress."""
    return "james.holden@scilifelab.se"


@pytest.fixture(name="case_id")
def fixture_case_id() -> str:
    """Return a case id."""
    return "yellowhog"


@pytest.fixture(name="another_case_id")
def fixture_another_case_id() -> str:
    """Return another case id."""
    return "another_case_id"


@pytest.fixture(name="sample_id")
def fixture_sample_id() -> str:
    """Returns a sample id."""
    return "ADM1"


@pytest.fixture(name="sample_name")
def fixture_sample_name() -> str:
    """Returns a sample name."""
    return "a_sample_name"


@pytest.fixture(name="cust_sample_id", scope="session")
def fixture_cust_sample_id() -> str:
    """Returns a customer sample id."""
    return "child"


@pytest.fixture(name="family_name")
def fixture_family_name() -> str:
    """Return a case name."""
    return "case"


@pytest.fixture(name="customer_id", scope="session")
def fixture_customer_id() -> str:
    """Return a customer id."""
    return "cust000"


@pytest.fixture(name="sbatch_job_number")
def fixture_sbatch_job_number() -> int:
    return 123456


@pytest.fixture(name="sbatch_process")
def fixture_sbatch_process(sbatch_job_number: int) -> ProcessMock:
    """Return a mocked process object."""
    slurm_process = ProcessMock(binary="sbatch")
    slurm_process.set_stdout(text=str(sbatch_job_number))
    return slurm_process


@pytest.fixture(scope="function", name="analysis_family_single_case")
def fixture_analysis_family_single(
    case_id: str, family_name: str, sample_id: str, ticket: str
) -> dict:
    """Build an example case."""
    return {
        "name": family_name,
        "internal_id": case_id,
        "data_analysis": str(Pipeline.MIP_DNA),
        "application_type": "wgs",
        "panels": ["IEM", "EP"],
        "tickets": ticket,
        "samples": [
            {
                "name": "proband",
                "sex": Gender.MALE,
                "internal_id": sample_id,
                "status": "affected",
                "original_ticket": ticket,
                "reads": 5000000000,
                "capture_kit": "GMSmyeloid",
            }
        ],
    }


@pytest.fixture(scope="function", name="analysis_family")
def fixture_analysis_family(case_id: str, family_name: str, sample_id: str, ticket: str) -> dict:
    """Return a dictionary with information from a analysis case."""
    return {
        "name": family_name,
        "internal_id": case_id,
        "data_analysis": str(Pipeline.MIP_DNA),
        "application_type": "wgs",
        "tickets": ticket,
        "panels": ["IEM", "EP"],
        "samples": [
            {
                "name": "child",
                "sex": Gender.MALE,
                "internal_id": sample_id,
                "father": "ADM2",
                "mother": "ADM3",
                "status": "affected",
                "original_ticket": ticket,
                "reads": 5000000,
                "capture_kit": "GMSmyeloid",
            },
            {
                "name": "father",
                "sex": Gender.MALE,
                "internal_id": "ADM2",
                "status": "unaffected",
                "original_ticket": ticket,
                "reads": 6000000,
                "capture_kit": "GMSmyeloid",
            },
            {
                "name": "mother",
                "sex": Gender.FEMALE,
                "internal_id": "ADM3",
                "status": "unaffected",
                "original_ticket": ticket,
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
        "bed_path": "path/to/bed",
        "pon_path": "path/to/pon",
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
    """Return a CG config dict."""
    return CGConfig(**base_config_dict)


@pytest.fixture(name="chanjo_config")
def fixture_chanjo_config() -> Dict[str, Dict[str, str]]:
    """Chanjo configs"""
    return {"chanjo": {"config_path": "chanjo_config", "binary_path": "chanjo"}}


@pytest.fixture
def crunchy_config_dict():
    """Crunchy configs."""
    return {
        "crunchy": {
            "conda_binary": "a conda binary",
            "cram_reference": "/path/to/fasta",
            "slurm": {"account": "mock_account", "mail_user": "mock_mail", "conda_env": "mock_env"},
        }
    }


@pytest.fixture(name="hk_config_dict")
def fixture_hk_config_dict(root_path):
    """Crunchy configs."""
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


@pytest.fixture(scope="function")
def madeline_api(madeline_output) -> MockMadelineAPI:
    """madeline_api fixture."""
    _api = MockMadelineAPI()
    _api.set_outpath(madeline_output)
    return _api


@pytest.fixture(name="ticket", scope="session")
def fixture_ticket_number() -> str:
    """Return a ticket number for testing."""
    return "123456"


@pytest.fixture(name="osticket")
def fixture_os_ticket(ticket: str) -> MockOsTicket:
    """Return a api that mock the os ticket api."""
    api = MockOsTicket()
    api.set_ticket_nr(ticket)
    return api


# Files fixtures

# Common file fixtures
@pytest.fixture(scope="session", name="fixtures_dir")
def fixture_fixtures_dir() -> Path:
    """Return the path to the fixtures dir."""
    return Path("tests", "fixtures")


@pytest.fixture(name="analysis_dir")
def fixture_analysis_dir(fixtures_dir: Path) -> Path:
    """Return the path to the analysis dir."""
    return Path(fixtures_dir, "analysis")


@pytest.fixture(name="apps_dir")
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


@pytest.fixture(scope="function", name="project_dir")
def fixture_project_dir(tmpdir_factory) -> Generator[Path, None, None]:
    """Path to a temporary directory where intermediate files can be stored."""
    yield Path(tmpdir_factory.mktemp("data"))


@pytest.fixture(scope="function")
def tmp_file(project_dir) -> Path:
    """Return a temp file path."""
    return Path(project_dir, "test")


@pytest.fixture(name="non_existing_file_path")
def fixture_non_existing_file_path(project_dir: Path) -> Path:
    """Return the path to a non existing file."""
    return Path(project_dir, "a_file.txt")


@pytest.fixture(name="content")
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


@pytest.fixture(name="sample1_cram")
def fixture_sample1_cram(mip_dna_analysis_dir: Path) -> Path:
    """Return the path to the cram file for sample 1."""
    return Path(mip_dna_analysis_dir, "adm1.cram")


@pytest.fixture(name="vcf_file")
def fixture_vcf_file(mip_dna_store_files: Path) -> Path:
    """Return the path to to a vcf file."""
    return Path(mip_dna_store_files, "yellowhog_clinical_selected.vcf")


@pytest.fixture(name="fastq_file")
def fixture_fastq_file(fastq_dir: Path) -> Path:
    """Return the path to to a fastq file."""
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


@pytest.fixture(scope="function", name="run_name")
def fixture_run_name() -> str:
    """Return the name of a fastq run."""
    return "fastq_run"


@pytest.fixture(scope="function", name="original_fastq_data")
def fixture_original_fastq_data(fastq_dir: Path, run_name) -> CompressionData:
    """Return a compression object with a path to the original fastq files."""
    return CompressionData(Path(fastq_dir, run_name))


@pytest.fixture(scope="function", name="fastq_stub")
def fixture_fastq_stub(project_dir: Path, run_name: str) -> Path:
    """Creates a path to the base format of a fastq run."""
    return Path(project_dir, run_name)


@pytest.fixture(scope="function", name="compression_object")
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


@pytest.fixture(name="demultiplex_fixtures")
def fixture_demultiplex_fixtures(apps_dir: Path) -> Path:
    """Return the path to the demultiplex fixtures."""
    return Path(apps_dir, "demultiplexing")


@pytest.fixture(name="novaseq_dragen_sample_sheet_path")
def fixture_novaseq_dragen_sample_sheet_path(demultiplex_fixtures: Path) -> Path:
    """Return the path to a novaseq bcl2fastq sample sheet."""
    return Path(demultiplex_fixtures, "SampleSheetS2_Dragen.csv")


@pytest.fixture(name="raw_lims_sample_dir")
def fixture_raw_lims_sample_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to the raw samples fixtures."""
    return Path(demultiplex_fixtures, "raw_lims_samples")


@pytest.fixture(name="demultiplexed_runs")
def fixture_demultiplexed_runs(demultiplex_fixtures: Path) -> Path:
    """Return the path to a dir with flow cells ready for demultiplexing."""
    return Path(demultiplex_fixtures, "demultiplexed-runs")


@pytest.fixture(name="demux_run_dir")
def fixture_demux_run_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to a dir with flow cells ready for demultiplexing."""
    return Path(demultiplex_fixtures, "flowcell-runs")


@pytest.fixture(name="flow_cell")
def fixture_flow_cell(demux_run_dir: Path, flow_cell_full_name: str) -> FlowCell:
    """Create a flow cell object with flow cell that is demultiplexed."""
    return FlowCell(flow_cell_path=Path(demux_run_dir, flow_cell_full_name))


@pytest.fixture(name="flow_cell_id")
def fixture_flow_cell_id(flow_cell: FlowCell) -> str:
    """Return flow cell id from flow cell object."""
    return flow_cell.id


@pytest.fixture(name="another_flow_cell_id")
def fixture_another_flow_cell_id() -> str:
    """Return another flow cell id."""
    return "HF57HDRXY"


@pytest.fixture(name="demultiplexing_delivery_file")
def fixture_demultiplexing_delivery_file(flow_cell: FlowCell) -> Path:
    """Return demultiplexing delivery started file."""
    return Path(flow_cell.path, DemultiplexingDirsAndFiles.DELIVERY)


@pytest.fixture(name="hiseq_x_tile_dir")
def fixture_hiseq_x_tile_dir(flow_cell: FlowCell) -> Path:
    """Return Hiseq X tile dir."""
    return Path(flow_cell.path, DemultiplexingDirsAndFiles.HiseqX_TILE_DIR)


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


@pytest.fixture(name="flow_cell_full_name")
def fixture_flow_cell_full_name() -> str:
    """Return full flow cell name."""
    return "201203_A00689_0200_AHVKJCDRXX"


# Genotype file fixture


@pytest.fixture(name="bcf_file")
def fixture_bcf_file(apps_dir: Path) -> Path:
    """Return the path to a BCF file."""
    return Path(apps_dir, "gt", "yellowhog.bcf")


# Housekeeper, Chanjo file fixtures


@pytest.fixture(scope="function", name="bed_file")
def fixture_bed_file(analysis_dir) -> Path:
    """Return the path to a bed file."""
    return Path(analysis_dir, "sample_coverage.bed")


# Helper fixtures


@pytest.fixture(name="helpers")
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


@pytest.fixture(scope="function", name="hk_bundle_data")
def fixture_hk_bundle_data(case_id: str, bed_file: Path, timestamp: dt.datetime) -> Dict[str, Any]:
    """Return some bundle data for Housekeeper."""
    return {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [{"path": bed_file.as_posix(), "archive": False, "tags": ["bed", "sample"]}],
    }


@pytest.fixture(scope="function", name="sample_hk_bundle_no_files")
def fixture_sample_hk_bundle_no_files(sample_id: str, timestamp: dt.datetime) -> dict:
    """Create a complete bundle mock for testing compression."""
    return {
        "name": sample_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [],
    }


@pytest.fixture(scope="function", name="case_hk_bundle_no_files")
def fixture_case_hk_bundle_no_files(case_id: str, timestamp: dt.datetime) -> dict:
    """Create a complete bundle mock for testing compression."""
    return {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [],
    }


@pytest.fixture(scope="function", name="compress_hk_fastq_bundle")
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
        before_timestamp = dt.datetime.timestamp(dt.datetime(2020, 1, 1))
        # Update the utime so file looks old
        os.utime(fastq_file, (before_timestamp, before_timestamp))
        fastq_file_info = {"path": str(fastq_file), "archive": False, "tags": ["fastq"]}

        hk_bundle_data["files"].append(fastq_file_info)
    return hk_bundle_data


@pytest.fixture(name="housekeeper_api")
def fixture_housekeeper_api(hk_config_dict: dict) -> MockHousekeeperAPI:
    """Setup Housekeeper store."""
    return MockHousekeeperAPI(hk_config_dict)


@pytest.fixture(scope="function", name="real_housekeeper_api")
def fixture_real_housekeeper_api(hk_config_dict: dict) -> HousekeeperAPI:
    """Setup a real Housekeeper store."""
    _api = HousekeeperAPI(hk_config_dict)
    _api.initialise_db()
    yield _api


@pytest.fixture(scope="function", name="populated_housekeeper_api")
def fixture_populated_housekeeper_api(
    housekeeper_api: MockHousekeeperAPI, hk_bundle_data: dict, helpers
) -> MockHousekeeperAPI:
    """Setup a Housekeeper store with some data."""
    hk_api = housekeeper_api
    helpers.ensure_hk_bundle(hk_api, hk_bundle_data)
    return hk_api


@pytest.fixture(scope="function", name="hk_version_obj")
def fixture_hk_version_obj(
    housekeeper_api: MockHousekeeperAPI, hk_bundle_data: dict, helpers
) -> hk_models.Version:
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


@pytest.fixture(scope="function", name="scout_api")
def fixture_scout_api() -> MockScoutAPI:
    """Setup Scout API."""
    return MockScoutAPI()


# Crunchy fixtures


@pytest.fixture(scope="function", name="crunchy_api")
def fixture_crunchy_api():
    """Setup Crunchy API."""
    return MockCrunchyAPI()


# Store fixtures


@pytest.fixture(scope="function", name="analysis_store")
def fixture_analysis_store(
    base_store: Store, analysis_family: dict, wgs_application_tag: str, helpers: StoreHelpers
) -> Generator[Store, None, None]:
    """Setup a store instance for testing analysis API."""
    helpers.ensure_case_from_dict(
        base_store, case_info=analysis_family, app_tag=wgs_application_tag
    )
    yield base_store


@pytest.fixture(scope="function", name="analysis_store_trio")
def fixture_analysis_store_trio(analysis_store: Store) -> Generator[Store, None, None]:
    """Setup a store instance with a trio loaded for testing analysis API."""
    yield analysis_store


@pytest.fixture(scope="function", name="analysis_store_single_case")
def fixture_analysis_store_single(
    base_store: Store, analysis_family_single_case: Store, helpers: StoreHelpers
):
    """Setup a store instance with a single ind case for testing analysis API."""
    helpers.ensure_case_from_dict(base_store, case_info=analysis_family_single_case)
    yield base_store


@pytest.fixture(scope="function", name="collaboration_id")
def fixture_collaboration_id() -> str:
    """Return a default customer group."""
    return "all_customers"


@pytest.fixture(scope="function", name="customer_production")
def fixture_customer_production(collaboration_id: str, customer_id: str) -> dict:
    """Return a dictionary with information about the prod customer."""
    return {
        "customer_id": customer_id,
        "name": "Production",
        "scout_access": True,
        "collaboration_id": collaboration_id,
    }


@pytest.fixture(scope="function", name="external_wgs_application_tag")
def fixture_external_wgs_application_tag() -> str:
    """Return the external WGS application tag."""
    return "WGXCUSC000"


@pytest.fixture(scope="function", name="external_wgs_info")
def fixture_external_wgs_info(external_wgs_application_tag: str) -> dict:
    """Return a dictionary with information external WGS application."""
    return {
        "application_tag": external_wgs_application_tag,
        "application_type": "wgs",
        "description": "External WGS",
        "is_external": True,
        "target_reads": 10,
    }


@pytest.fixture(scope="function", name="external_wes_application_tag")
def fixture_external_wes_application_tag() -> str:
    """Return the external whole exome sequencing application tag."""
    return "EXXCUSR000"


@pytest.fixture(scope="function", name="external_wes_info")
def fixture_external_wes_info(external_wes_application_tag: str) -> dict:
    """Return a dictionary with information external WES application."""
    return {
        "application_tag": external_wes_application_tag,
        "application_type": "wes",
        "description": "External WES",
        "is_external": True,
        "target_reads": 10,
    }


@pytest.fixture(scope="function", name="wgs_application_tag")
def fixture_wgs_application_tag() -> str:
    """Return the WGS application tag."""
    return "WGSPCFC030"


@pytest.fixture(scope="function", name="wgs_application_info")
def fixture_wgs_application_info(wgs_application_tag: str) -> dict:
    """Return a dictionary with information the WGS application."""
    return {
        "application_tag": wgs_application_tag,
        "application_type": "wgs",
        "description": "WGS, double",
        "sequencing_depth": 30,
        "is_external": True,
        "is_accredited": True,
        "target_reads": 10,
    }


@pytest.fixture(name="store")
def fixture_store() -> Store:
    """Fixture with a CG store."""
    _store = Store(uri="sqlite:///")
    _store.create_all()
    yield _store
    _store.drop_all()


@pytest.fixture(name="apptag_rna")
def fixture_apptag_rna() -> str:
    """Return the RNA application tag."""
    return "RNAPOAR025"


@pytest.fixture(scope="function", name="base_store")
def fixture_base_store(store: Store, apptag_rna: str, customer_id: str) -> Store:
    """Setup and example store."""
    collaboration = store.add_collaboration("all_customers", "all customers")

    store.add_commit(collaboration)
    customers = [
        store.add_customer(
            customer_id,
            "Production",
            scout_access=True,
            invoice_address="Test street",
            invoice_reference="ABCDEF",
        ),
        store.add_customer(
            "cust001",
            "Customer",
            scout_access=False,
            invoice_address="Test street",
            invoice_reference="ABCDEF",
        ),
        store.add_customer(
            "cust002",
            "Karolinska",
            scout_access=True,
            invoice_address="Test street",
            invoice_reference="ABCDEF",
        ),
        store.add_customer(
            "cust003",
            "CMMS",
            scout_access=True,
            invoice_address="Test street",
            invoice_reference="ABCDEF",
        ),
    ]
    for customer in customers:
        collaboration.customers.append(customer)
    store.add_commit(customers)
    applications = [
        store.add_application(
            tag="WGXCUSC000",
            category="wgs",
            description="External WGS",
            sequencing_depth=0,
            is_external=True,
            percent_kth=80,
            percent_reads_guaranteed=75,
            target_reads=10,
        ),
        store.add_application(
            tag="EXXCUSR000",
            category="wes",
            description="External WES",
            sequencing_depth=0,
            is_external=True,
            percent_kth=80,
            percent_reads_guaranteed=75,
            target_reads=10,
        ),
        store.add_application(
            tag="WGSPCFC060",
            category="wgs",
            description="WGS, double",
            sequencing_depth=30,
            accredited=True,
            percent_kth=80,
            percent_reads_guaranteed=75,
            target_reads=10,
        ),
        store.add_application(
            tag="RMLP05R800",
            category="rml",
            description="Ready-made",
            sequencing_depth=0,
            percent_kth=80,
            percent_reads_guaranteed=75,
            target_reads=10,
        ),
        store.add_application(
            tag="WGSPCFC030",
            category="wgs",
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
            category="wgs",
            description="Whole genome metagenomics",
            sequencing_depth=0,
            target_reads=400000,
            percent_kth=80,
            percent_reads_guaranteed=75,
        ),
        store.add_application(
            tag="METNXTR020",
            category="wgs",
            description="Metagenomics",
            sequencing_depth=0,
            target_reads=200000,
            percent_kth=80,
            percent_reads_guaranteed=75,
        ),
        store.add_application(
            tag="MWRNXTR003",
            category="mic",
            description="Microbial whole genome ",
            sequencing_depth=0,
            percent_kth=80,
            percent_reads_guaranteed=75,
            target_reads=10,
        ),
        store.add_application(
            tag=apptag_rna,
            category="tgs",
            description="RNA seq, poly-A based priming",
            percent_kth=80,
            percent_reads_guaranteed=75,
            sequencing_depth=25,
            accredited=True,
            target_reads=10,
            min_sequencing_depth=30,
        ),
        store.add_application(
            tag="VWGDPTR001",
            category="cov",
            description="Viral whole genome  ",
            sequencing_depth=0,
            percent_kth=80,
            percent_reads_guaranteed=75,
            target_reads=10,
        ),
    ]

    store.add_commit(applications)

    prices = {"standard": 10, "priority": 20, "express": 30, "research": 5}
    versions = [
        store.add_version(application, 1, valid_from=dt.datetime.now(), prices=prices)
        for application in applications
    ]
    store.add_commit(versions)

    beds = [store.add_bed("Bed")]
    store.add_commit(beds)
    bed_versions = [store.add_bed_version(bed, 1, "Bed.bed") for bed in beds]
    store.add_commit(bed_versions)

    organism = store.add_organism("C. jejuni", "C. jejuni")
    store.add_commit(organism)

    yield store


@pytest.fixture(scope="function")
def sample_store(base_store: Store) -> Store:
    """Populate store with samples."""
    new_samples = [
        base_store.add_sample("ordered", sex=Gender.MALE),
        base_store.add_sample("received", sex=Gender.UNKNOWN, received=dt.datetime.now()),
        base_store.add_sample(
            "received-prepared",
            sex=Gender.UNKNOWN,
            received=dt.datetime.now(),
            prepared_at=dt.datetime.now(),
        ),
        base_store.add_sample("external", sex=Gender.FEMALE, external=True),
        base_store.add_sample(
            "external-received", sex=Gender.FEMALE, received=dt.datetime.now(), external=True
        ),
        base_store.add_sample(
            "sequenced",
            sex=Gender.MALE,
            received=dt.datetime.now(),
            prepared_at=dt.datetime.now(),
            sequenced_at=dt.datetime.now(),
            reads=(310 * 1000000),
        ),
        base_store.add_sample(
            "sequenced-partly",
            sex=Gender.MALE,
            received=dt.datetime.now(),
            prepared_at=dt.datetime.now(),
            reads=(250 * 1000000),
        ),
    ]
    customer = base_store.customers().first()
    external_app = base_store.application("WGXCUSC000").versions[0]
    wgs_app = base_store.application("WGSPCFC030").versions[0]
    for sample in new_samples:
        sample.customer = customer
        sample.application_version = external_app if "external" in sample.name else wgs_app
    base_store.add_commit(new_samples)
    return base_store


@pytest.fixture(scope="function", name="trailblazer_api")
def fixture_trailblazer_api() -> MockTB:
    """Return a mock traailblazer API."""
    return MockTB()


@pytest.fixture(scope="function", name="lims_api")
def fixture_lims_api() -> MockLimsAPI:
    """Return a mock LIMS API."""
    return MockLimsAPI()


@pytest.fixture(name="config_root_dir")
def config_root_dir(tmpdir_factory) -> Path:
    """Return a path to the config root directory."""
    return Path("tests/fixtures/data")


@pytest.fixture()
def housekeeper_dir(tmpdir_factory):
    """Return a temporary directory for Housekeeper testing."""
    return tmpdir_factory.mktemp("housekeeper")


@pytest.fixture()
def mip_dir(tmpdir_factory) -> Path:
    """Return a temporary directory for MIP testing."""
    return tmpdir_factory.mktemp("mip")


@pytest.fixture(scope="function")
def fluffy_dir(tmpdir_factory) -> Path:
    """Return a temporary directory for Fluffy testing."""
    return tmpdir_factory.mktemp("fluffy")


@pytest.fixture(scope="function")
def balsamic_dir(tmpdir_factory) -> Path:
    """Return a temporary directory for Balsamic testing."""
    return tmpdir_factory.mktemp("balsamic")


@pytest.fixture(scope="function")
def cg_dir(tmpdir_factory) -> Path:
    """Return a temporary directory for cg testing."""
    return tmpdir_factory.mktemp("cg")


@pytest.fixture(scope="function")
def microsalt_dir(tmpdir_factory) -> Path:
    """Return a temporary directory for Microsalt testing."""
    return tmpdir_factory.mktemp("microsalt")


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
) -> dict:
    """Return a context config."""
    return {
        "bed_path": str(cg_dir),
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
            "encrypt_dir": "/home/ENCRYPT/",
            "root": {"hiseqx": "flowcells/hiseqx", "hiseqga": "RUNS/", "novaseq": "runs/"},
        },
        "balsamic": {
            "balsamic_cache": "hello",
            "binary_path": "echo",
            "conda_env": "S_BALSAMIC",
            "root": str(balsamic_dir),
            "slurm": {
                "account": "development",
                "mail_user": "test.email@scilifelab.se",
                "qos": SlurmQos.LOW,
            },
        },
        "cgstats": {"binary_path": "echo", "database": "sqlite:///./cgstats", "root": str(cg_dir)},
        "chanjo": {"binary_path": "echo", "config_path": "chanjo-stage.yaml"},
        "crunchy": {
            "conda_binary": "a_conda_binary",
            "cram_reference": "grch37_homo_sapiens_-d5-.fasta",
            "slurm": {
                "account": "development",
                "conda_env": "S_crunchy",
                "mail_user": "an@scilifelab.se",
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
            "run_dir": "tests/fixtures/apps/demultiplexing/flowcell-runs",
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
        "pdc": {"binary_path": "/bin/dsmc"},
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
        "vogue": {"binary_path": "echo", "config_path": "vogue-stage.yaml"},
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
