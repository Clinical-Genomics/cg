"""Conftest file for pytest fixtures that needs to be shared for multiple tests."""

import gzip
import http
import logging
import os
import shutil
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any, Generator

import pytest
from pytest_mock import MockFixture
from housekeeper.store.models import File, Version
from requests import Response

from cg.apps.crunchy import CrunchyAPI
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.demultiplex.sample_sheet.api import IlluminaSampleSheetService
from cg.apps.downsample.downsample import DownsampleAPI
from cg.apps.gens import GensAPI
from cg.apps.gt import GenotypeAPI
from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.housekeeper.models import InputBundle
from cg.apps.lims import LimsAPI
from cg.apps.slurm.slurm_api import SlurmAPI
from cg.apps.tb.dto.summary_response import AnalysisSummary, StatusSummary
from cg.clients.freshdesk.freshdesk_client import FreshdeskClient
from cg.constants import FileExtensions, SequencingFileTag, Workflow
from cg.constants.constants import (
    CaseActions,
    CustomerId,
    FileFormat,
    GenomeVersion,
    Strandedness,
)
from cg.constants.gene_panel import GenePanelMasterList
from cg.constants.housekeeper_tags import HK_DELIVERY_REPORT_TAG
from cg.constants.priority import SlurmQos
from cg.constants.scout import ScoutExportFileName
from cg.constants.sequencing import SequencingPlatform
from cg.constants.subject import Sex
from cg.constants.tb import AnalysisTypes
from cg.io.controller import ReadFile, WriteFile
from cg.io.json import read_json, write_json
from cg.io.yaml import read_yaml, write_yaml
from cg.meta.tar.tar import TarAPI
from cg.meta.transfer.external_data import ExternalDataAPI
from cg.meta.workflow.jasen import JasenAnalysisAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.meta.workflow.tomte import TomteAnalysisAPI
from cg.models import CompressionData
from cg.models.cg_config import CGConfig, PDCArchivingDirectory
from cg.models.downsample.downsample_data import DownsampleData
from cg.models.raredisease.raredisease import (
    RarediseaseParameters,
    RarediseaseSampleSheetHeaders,
)
from cg.models.rnafusion.rnafusion import RnafusionParameters, RnafusionSampleSheetEntry
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.models.taxprofiler.taxprofiler import (
    TaxprofilerParameters,
    TaxprofilerSampleSheetEntry,
)
from cg.models.tomte.tomte import TomteParameters, TomteSampleSheetHeaders
from cg.services.deliver_files.rsync.service import (
    DeliveryRsyncService,
)
from cg.services.illumina.backup.encrypt_service import IlluminaRunEncryptionService
from cg.services.illumina.data_transfer.data_transfer_service import (
    IlluminaDataTransferService,
)
from cg.store.database import create_all_tables, drop_all_tables, initialize_database
from cg.store.models import (
    Application,
    ApplicationVersion,
    Bed,
    BedVersion,
    Case,
    Customer,
    IlluminaSequencingRun,
    Order,
    Organism,
    Sample,
)
from cg.store.store import Store
from cg.utils import Process
from tests.mocks.crunchy import MockCrunchyAPI
from tests.mocks.hk_mock import MockHousekeeperAPI
from tests.mocks.limsmock import LimsSample, LimsUDF, MockLimsAPI
from tests.mocks.madeline import MockMadelineAPI
from tests.mocks.process_mock import ProcessMock
from tests.mocks.scout import MockScoutAPI
from tests.mocks.tb_mock import MockTB
from tests.small_helpers import SmallHelpers
from tests.store_helpers import StoreHelpers

LOG = logging.getLogger(__name__)
multiqc_json_file = "multiqc_data.json"
software_version_file = "software_versions.yml"
deliverables_yaml = "_deliverables.yaml"
pytest_plugins = [
    "tests.fixture_plugins.backup_fixtures.backup_fixtures",
    "tests.fixture_plugins.chanjo2_fixtures.api_fixtures",
    "tests.fixture_plugins.chanjo2_fixtures.models_fixtures",
    "tests.fixture_plugins.delivery_fixtures.bundle_fixtures",
    "tests.fixture_plugins.delivery_fixtures.context_fixtures",
    "tests.fixture_plugins.delivery_fixtures.path_fixtures",
    "tests.fixture_plugins.delivery_report_fixtures.api_fixtures",
    "tests.fixture_plugins.delivery_report_fixtures.context_fixtures",
    "tests.fixture_plugins.delivery_fixtures.delivery_files_models_fixtures",
    "tests.fixture_plugins.delivery_fixtures.delivery_services_fixtures",
    "tests.fixture_plugins.delivery_fixtures.delivery_formatted_files_fixtures",
    "tests.fixture_plugins.demultiplex_fixtures.flow_cell_fixtures",
    "tests.fixture_plugins.demultiplex_fixtures.housekeeper_fixtures",
    "tests.fixture_plugins.demultiplex_fixtures.metrics_fixtures",
    "tests.fixture_plugins.demultiplex_fixtures.name_fixtures",
    "tests.fixture_plugins.demultiplex_fixtures.path_fixtures",
    "tests.fixture_plugins.demultiplex_fixtures.run_parameters_fixtures",
    "tests.fixture_plugins.demultiplex_fixtures.sample_fixtures",
    "tests.fixture_plugins.demultiplex_fixtures.sample_sheet_fixtures",
    "tests.fixture_plugins.device_fixtures",
    "tests.fixture_plugins.encryption_fixtures.encryption_fixtures",
    "tests.fixture_plugins.fohm.fohm_fixtures",
    "tests.fixture_plugins.io.csv_fixtures",
    "tests.fixture_plugins.illumina_clean_fixtures.clean_fixtures",
    "tests.fixture_plugins.loqusdb_fixtures.loqusdb_api_fixtures",
    "tests.fixture_plugins.loqusdb_fixtures.loqusdb_output_fixtures",
    "tests.fixture_plugins.observations_fixtures.observations_api_fixtures",
    "tests.fixture_plugins.observations_fixtures.observations_input_files_fixtures",
    "tests.fixture_plugins.orders_fixtures.order_form_fixtures",
    "tests.fixture_plugins.orders_fixtures.order_store_service_fixtures",
    "tests.fixture_plugins.orders_fixtures.order_to_submit_fixtures",
    "tests.fixture_plugins.orders_fixtures.status_data_fixtures",
    "tests.fixture_plugins.pacbio_fixtures.context_fixtures",
    "tests.fixture_plugins.pacbio_fixtures.dto_fixtures",
    "tests.fixture_plugins.pacbio_fixtures.file_data_fixtures",
    "tests.fixture_plugins.pacbio_fixtures.metrics_fixtures",
    "tests.fixture_plugins.pacbio_fixtures.name_fixtures",
    "tests.fixture_plugins.pacbio_fixtures.path_fixtures",
    "tests.fixture_plugins.pacbio_fixtures.run_data_fixtures",
    "tests.fixture_plugins.pacbio_fixtures.service_fixtures",
    "tests.fixture_plugins.pacbio_fixtures.unprocessed_runs_fixtures",
    "tests.fixture_plugins.quality_controller_fixtures.sequencing_qc_check_scenario",
    "tests.fixture_plugins.quality_controller_fixtures.sequencing_qc_fixtures",
    "tests.fixture_plugins.timestamp_fixtures",
]


# Case fixtures


@pytest.fixture(scope="session")
def any_string() -> str:
    return "any_string"


@pytest.fixture(scope="session")
def slurm_account() -> str:
    """Return a SLURM account."""
    return "super_account"


@pytest.fixture(scope="session")
def user_name() -> str:
    """Return a username."""
    return "Paul Anderson"


@pytest.fixture(scope="session")
def user_mail() -> str:
    """Return a user email."""
    return "paul@magnolia.com"


@pytest.fixture(scope="function")
def email_address() -> str:
    """Return an email address."""
    return "user.name@scilifelab.se"


@pytest.fixture(scope="session")
def case_id() -> str:
    """Return a case id."""
    return "yellowhog"


@pytest.fixture(scope="session")
def case_name() -> str:
    return "C12345"


@pytest.fixture(scope="session")
def case_id_does_not_exist() -> str:
    """Return a case id that should not exist."""
    return "case_does_not_exist"


@pytest.fixture(scope="session")
def another_case_id() -> str:
    """Return another case id."""
    return "another_case_id"


@pytest.fixture(scope="session")
def sample_id() -> str:
    """Return a sample id."""
    return "ADM1"


@pytest.fixture(scope="session")
def another_sample_id() -> str:
    """Return another sample id."""
    return "another_sample_id"


@pytest.fixture(scope="session")
def father_sample_id() -> str:
    """Return the sample id of the father."""
    return "ADM2"


@pytest.fixture(scope="session")
def mother_sample_id() -> str:
    """Return the mothers sample id."""
    return "ADM3"


@pytest.fixture(scope="session")
def invalid_sample_id() -> str:
    """Return an invalid sample id."""
    return "invalid-sample-id"


@pytest.fixture(scope="session")
def sample_ids(sample_id: str, father_sample_id: str, mother_sample_id: str) -> list[str]:
    """Return a list with three samples of a family."""
    return [sample_id, father_sample_id, mother_sample_id]


@pytest.fixture(scope="session")
def sample_name() -> str:
    """Returns a sample name."""
    return "a_sample_name"


@pytest.fixture(scope="session")
def another_sample_name() -> str:
    """Returns a sample name."""
    return "another_sample_name"


@pytest.fixture(scope="session")
def cust_sample_id() -> str:
    """Returns a customer sample id."""
    return "child"


@pytest.fixture(scope="session")
def family_name() -> str:
    """Return a case name."""
    return "case"


@pytest.fixture(scope="session")
def customer_id() -> str:
    """Return a customer id."""
    return "cust000"


@pytest.fixture(scope="session")
def sbatch_job_number() -> int:
    return 123456


@pytest.fixture(scope="session")
def empty_list() -> list:
    return []


@pytest.fixture(scope="session")
def sbatch_process(sbatch_job_number: int) -> ProcessMock:
    """Return a mocked process object."""
    slurm_process = ProcessMock(binary="sbatch")
    slurm_process.set_stdout(text=str(sbatch_job_number))
    return slurm_process


@pytest.fixture(scope="function")
def dna_case(analysis_store, helpers) -> Case:
    """Case with DNA application"""
    cust = helpers.ensure_customer(analysis_store)
    return analysis_store.get_case_by_name_and_customer(customer=cust, case_name="dna_case")


@pytest.fixture
def analysis_family_single_case(
    case_id: str, family_name: str, sample_id: str, ticket_id: str
) -> dict:
    """Build an example case."""
    return {
        "name": family_name,
        "internal_id": case_id,
        "data_analysis": Workflow.MIP_DNA,
        "application_type": "wgs",
        "panels": ["IEM", "EP"],
        "tickets": ticket_id,
        "samples": [
            {
                "name": "proband",
                "sex": Sex.MALE,
                "internal_id": sample_id,
                "status": "affected",
                "original_ticket": ticket_id,
                "reads": 5000000000,
                "capture_kit": "GMSmyeloid",
            }
        ],
    }


@pytest.fixture
def analysis_family(case_id: str, family_name: str, sample_id: str, ticket_id: str) -> dict:
    """Return a dictionary with information from a analysis case."""
    return {
        "name": family_name,
        "internal_id": case_id,
        "data_analysis": Workflow.MIP_DNA,
        "application_type": "wgs",
        "tickets": ticket_id,
        "panels": ["IEM", "EP"],
        "samples": [
            {
                "name": "child",
                "sex": Sex.MALE,
                "internal_id": sample_id,
                "father": "ADM2",
                "mother": "ADM3",
                "status": "affected",
                "original_ticket": ticket_id,
                "reads": 5000000,
                "capture_kit": "GMSmyeloid",
                "reference_genome": GenomeVersion.GRCh37,
            },
            {
                "name": "father",
                "sex": Sex.MALE,
                "internal_id": "ADM2",
                "status": "unaffected",
                "original_ticket": ticket_id,
                "reads": 6000000,
                "capture_kit": "GMSmyeloid",
                "reference_genome": GenomeVersion.GRCh37,
            },
            {
                "name": "mother",
                "sex": Sex.FEMALE,
                "internal_id": "ADM3",
                "status": "unaffected",
                "original_ticket": ticket_id,
                "reads": 7000000,
                "capture_kit": "GMSmyeloid",
                "reference_genome": GenomeVersion.GRCh37,
            },
        ],
    }


# Config fixtures


@pytest.fixture
def base_config_dict() -> dict:
    """Returns the basic configs necessary for running CG."""
    return {
        "database": "sqlite:///",
        "madeline_exe": "path/to/madeline",
        "tower_binary_path": "path/to/tower",
        "delivery_path": "path/to/delivery",
        "nanopore_data_directory": "path/to/nanopore_data_directory",
        "run_instruments": {
            "pacbio": {
                "data_dir": "path/to/data_directory",
                "systemd_trigger_dir": "path/to/trigger_directory",
            },
            "nanopore": {
                "data_dir": "path/to/data_directory",
                "systemd_trigger_dir": "path/to/ptrigger_directory",
            },
            "illumina": {
                "sequencing_runs_dir": "path/to/sequencing-runs",
                "demultiplexed_runs_dir": "path/to/demultiplexed_flow_cells_dir",
            },
        },
        "downsample": {
            "downsample_dir": "path/to/downsample_dir",
            "downsample_script": "downsample.sh",
            "account": "development",
        },
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
        "sentieon_licence_server": "127.0.0.1:8080",
    }


@pytest.fixture
def cg_config_object(base_config_dict: dict) -> CGConfig:
    """Return a CG config."""
    return CGConfig(**base_config_dict)


@pytest.fixture
def chanjo_config() -> dict[str, dict[str, str]]:
    """Return Chanjo config."""
    return {"chanjo": {"config_path": "chanjo_config", "binary_path": "chanjo"}}


@pytest.fixture
def crunchy_config() -> dict[str, dict[str, Any]]:
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


@pytest.fixture
def demultiplexing_context_for_demux(
    demultiplexing_api_for_demux: DemultiplexingAPI,
    cg_context: CGConfig,
    store_with_illumina_sequencing_data: Store,
) -> CGConfig:
    """Return cg context with a demultiplex context."""
    cg_context.demultiplex_api_ = demultiplexing_api_for_demux
    cg_context.housekeeper_api_ = demultiplexing_api_for_demux.hk_api
    cg_context.status_db_ = store_with_illumina_sequencing_data
    return cg_context


@pytest.fixture
def demultiplex_context(
    demultiplexing_api: DemultiplexingAPI,
    illumina_demultiplexed_runs_post_processing_hk_api: HousekeeperAPI,
    cg_context: CGConfig,
    tmp_illumina_demultiplexed_runs_directory: Path,
    store_with_illumina_sequencing_data: Store,
) -> CGConfig:
    """Return cg context with a demultiplex context."""
    cg_context.demultiplex_api_ = demultiplexing_api
    cg_context.run_instruments.illumina.demultiplexed_runs_dir = (
        tmp_illumina_demultiplexed_runs_directory.as_posix()
    )
    cg_context.housekeeper_api_ = illumina_demultiplexed_runs_post_processing_hk_api
    cg_context.status_db_ = store_with_illumina_sequencing_data
    return cg_context


@pytest.fixture
def new_demultiplex_context(
    demultiplexing_api: DemultiplexingAPI,
    real_housekeeper_api: HousekeeperAPI,
    cg_context: CGConfig,
    store_with_illumina_sequencing_data: Store,
) -> CGConfig:
    """Return a CG context with populated with data using the Illumina models."""
    cg_context.demultiplex_api_ = demultiplexing_api
    cg_context.housekeeper_api_ = real_housekeeper_api
    cg_context.status_db_ = store_with_illumina_sequencing_data
    return cg_context


@pytest.fixture(name="demultiplex_configs_for_demux")
def demultiplex_configs_for_demux(
    tmp_illumina_flow_cells_demux_all_directory,
    tmp_empty_demultiplexed_runs_directory: Path,
) -> dict:
    """Return demultiplex configs."""
    return {
        "run_instruments": {
            "illumina": {
                "sequencing_runs_dir": tmp_illumina_flow_cells_demux_all_directory.as_posix(),
                "demultiplexed_runs_dir": tmp_empty_demultiplexed_runs_directory.as_posix(),
            }
        },
        "demultiplex": {"slurm": {"account": "test", "mail_user": "testuser@github.se"}},
    }


@pytest.fixture(name="demultiplex_configs")
def demultiplex_configs(
    tmp_illumina_sequencing_runs_directory,
    tmp_illumina_demultiplexed_flow_cells_directory,
) -> dict:
    """Return demultiplex configs."""
    return {
        "run_instruments": {
            "illumina": {
                "sequencing_runs_dir": tmp_illumina_sequencing_runs_directory.as_posix(),
                "demultiplexed_runs_dir": tmp_illumina_demultiplexed_flow_cells_directory.as_posix(),
            }
        },
        "demultiplex": {"slurm": {"account": "test", "mail_user": "testuser@github.se"}},
    }


@pytest.fixture
def real_crunchy_api(crunchy_config) -> CrunchyAPI:
    return CrunchyAPI(crunchy_config)


@pytest.fixture
def hk_config_dict(root_path: Path):
    """Housekeeper configs."""
    return {
        "housekeeper": {
            "database": "sqlite:///:memory:",
            "root": str(root_path),
        }
    }


@pytest.fixture
def genotype_config() -> dict:
    """Genotype config fixture."""
    return {
        "genotype": {
            "database": "database",
            "config_path": "config/path",
            "binary_path": "gtdb",
        }
    }


@pytest.fixture
def gens_config() -> dict[str, dict[str, str]]:
    """Gens config fixture."""
    return {
        "gens": {
            "config_path": Path("config", "path").as_posix(),
            "binary_path": "gens",
        }
    }


@pytest.fixture(name="sample_sheet_context")
def sample_sheet_context(
    cg_context: CGConfig,
    lims_api: LimsAPI,
    populated_housekeeper_api: HousekeeperAPI,
    tmp_illumina_sequencing_runs_directory: Path,
) -> CGConfig:
    """Return cg context with added Lims and Housekeeper API."""
    cg_context.lims_api_ = lims_api
    cg_context.housekeeper_api_ = populated_housekeeper_api
    cg_context.sample_sheet_api_ = IlluminaSampleSheetService(
        flow_cell_dir=tmp_illumina_sequencing_runs_directory.as_posix(),
        hk_api=cg_context.housekeeper_api,
        lims_api=cg_context.lims_api,
    )
    return cg_context


@pytest.fixture
def sample_sheet_context_broken_flow_cells(
    cg_context: CGConfig,
    lims_api: LimsAPI,
    populated_housekeeper_api: HousekeeperAPI,
    tmp_broken_flow_cells_directory: Path,
) -> CGConfig:
    """Return cg context with broken flow cells."""
    cg_context.run_instruments.illumina.demultiplexed_runs_dir = (
        tmp_broken_flow_cells_directory.as_posix()
    )
    cg_context.lims_api_ = lims_api
    cg_context.housekeeper_api_ = populated_housekeeper_api
    cg_context.sample_sheet_api_ = IlluminaSampleSheetService(
        flow_cell_dir=tmp_broken_flow_cells_directory.as_posix(),
        hk_api=cg_context.housekeeper_api,
        lims_api=cg_context.lims_api,
    )
    return cg_context


# Api fixtures


@pytest.fixture(name="demultiplexing_api_for_demux")
def demultiplexing_api_for_demux(
    demultiplex_configs_for_demux: dict,
    sbatch_process: Process,
    populated_housekeeper_api: HousekeeperAPI,
) -> DemultiplexingAPI:
    """Return demultiplex API."""
    demux_api = DemultiplexingAPI(
        config=demultiplex_configs_for_demux,
        housekeeper_api=populated_housekeeper_api,
    )
    demux_api.slurm_api.process = sbatch_process
    return demux_api


@pytest.fixture
def demultiplexing_api(
    demultiplex_configs: dict, sbatch_process: Process, populated_housekeeper_api: HousekeeperAPI
) -> DemultiplexingAPI:
    """Return demultiplex API."""
    demux_api = DemultiplexingAPI(
        config=demultiplex_configs, housekeeper_api=populated_housekeeper_api
    )
    demux_api.slurm_api.process = sbatch_process
    return demux_api


@pytest.fixture
def delivery_rsync_service(cg_context: CGConfig) -> DeliveryRsyncService:
    """Delivery Rsync service fixture."""
    return cg_context.delivery_rsync_service


@pytest.fixture
def external_data_api(analysis_store, cg_context: CGConfig) -> ExternalDataAPI:
    """ExternalDataAPI fixture."""
    return ExternalDataAPI(config=cg_context)


@pytest.fixture
def genotype_api(genotype_config: dict) -> GenotypeAPI:
    """Genotype API fixture."""
    _genotype_api = GenotypeAPI(genotype_config)
    _genotype_api.set_dry_run(True)
    return _genotype_api


@pytest.fixture
def gens_api(gens_config: dict) -> GensAPI:
    """Gens API fixture."""
    _gens_api = GensAPI(gens_config)
    _gens_api.set_dry_run(True)
    return _gens_api


@pytest.fixture
def madeline_api(madeline_output: Path) -> MockMadelineAPI:
    """madeline_api fixture."""
    _api = MockMadelineAPI()
    _api.set_outpath(out_path=madeline_output.as_posix())
    return _api


@pytest.fixture(scope="session")
def ticket_id() -> str:
    """Return a ticket number for testing."""
    return "123456"


@pytest.fixture
def freshdesk_client() -> FreshdeskClient:
    """Return a FreshdeskClient instance with mock parameters."""
    client = FreshdeskClient(base_url="https://mock.freshdesk.com", api_key="mock_api_key")
    return client


# Files fixtures


@pytest.fixture
def empty_fastq_file_path(data_dir: Path):
    """Return the path to an empty fastq file."""
    return Path(data_dir, "fastq.fastq.gz")


# Common file name fixtures


@pytest.fixture
def snv_vcf_file() -> str:
    """Return a single nucleotide variant file name."""
    return f"snv{FileExtensions.VCF}"


@pytest.fixture
def sv_vcf_file() -> str:
    """Return a structural variant file name."""
    return f"sv{FileExtensions.VCF}"


@pytest.fixture
def snv_research_vcf_file() -> str:
    #    """Return a single nucleotide variant research file name."""
    return f"snv_research{FileExtensions.VCF}"


@pytest.fixture
def sv_research_vcf_file() -> str:
    """Return a structural variant research file name."""
    return f"sv_research{FileExtensions.VCF}"


# Common file fixtures
@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Return the path to the fixtures dir."""
    return Path("tests", "fixtures")


@pytest.fixture(scope="session")
def analysis_dir(fixtures_dir: Path) -> Path:
    """Return the path to the analysis dir."""
    return Path(fixtures_dir, "analysis")


@pytest.fixture(scope="session")
def microsalt_analysis_dir(analysis_dir: Path) -> Path:
    """Return the path to the analysis dir."""
    return Path(analysis_dir, "microsalt")


@pytest.fixture(scope="session")
def mutant_analysis_dir(analysis_dir: Path) -> Path:
    """Return the path to the mutant analysis directory"""
    return Path(analysis_dir, "mutant")


@pytest.fixture(scope="session")
def apps_dir(fixtures_dir: Path) -> Path:
    """Return the path to the apps dir."""
    return Path(fixtures_dir, "apps")


@pytest.fixture(scope="session")
def cgweb_orders_dir(fixtures_dir: Path) -> Path:
    """Return the path to the cgweb_orders dir."""
    return Path(fixtures_dir, "cgweb_orders")


@pytest.fixture(scope="session")
def data_dir(fixtures_dir: Path) -> Path:
    """Return the path to the data dir."""
    return Path(fixtures_dir, "data")


@pytest.fixture(scope="session")
def devices_dir(fixtures_dir: Path) -> Path:
    """Return the path to the device dir."""
    return Path(fixtures_dir, "devices")


@pytest.fixture
def project_dir(tmpdir_factory) -> Generator[Path, None, None]:
    """Path to a temporary directory where intermediate files can be stored."""
    yield Path(tmpdir_factory.mktemp("data"))


@pytest.fixture
def tmp_file(project_dir) -> Path:
    """Return a temp file path."""
    return Path(project_dir, "test")


@pytest.fixture
def non_existing_file_path(project_dir: Path) -> Path:
    """Return the path to a non-existing file."""
    return Path(project_dir, "a_file.txt")


@pytest.fixture(scope="session")
def content() -> str:
    """Return some content for a file."""
    return (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt"
        " ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ull"
        "amco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehende"
        "rit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaec"
        "at cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
    )


@pytest.fixture
def filled_file(non_existing_file_path: Path, content: str) -> Path:
    """Return the path to an existing file with some content."""
    with open(non_existing_file_path, "w") as outfile:
        outfile.write(content)
    return non_existing_file_path


@pytest.fixture(scope="session")
def orderforms(fixtures_dir: Path) -> Path:
    """Return the path to the directory with order forms."""
    return Path(fixtures_dir, "orderforms")


@pytest.fixture
def hk_file(filled_file: Path, case_id: str) -> File:
    """Return a housekeeper File object."""
    return File(id=case_id, path=filled_file.as_posix())


@pytest.fixture
def mip_dna_store_files(apps_dir: Path) -> Path:
    """Return the path to the directory with mip dna store files."""
    return Path(apps_dir, "mip", "dna", "store")


@pytest.fixture
def case_qc_sample_info_path(mip_dna_store_files: Path) -> Path:
    """Return path to case_qc_sample_info.yaml."""
    return Path(mip_dna_store_files, "case_qc_sample_info.yaml")


@pytest.fixture
def delivery_report_html(mip_dna_store_files: Path) -> Path:
    """Return the path to a qc metrics deliverables file with case data."""
    return Path(mip_dna_store_files, "empty_delivery_report.html")


@pytest.fixture
def mip_deliverables_file(mip_dna_store_files: Path) -> Path:
    """Fixture for general deliverables file in mip."""
    return Path(mip_dna_store_files, "case_id_deliverables.yaml")


@pytest.fixture
def case_qc_metrics_deliverables(apps_dir: Path) -> Path:
    """Return the path to a qc metrics deliverables file with case data."""
    return Path(apps_dir, "mip", "case_metrics_deliverables.yaml")


@pytest.fixture
def case_qc_metrics_deliverables_raredisease(apps_dir: Path) -> Path:
    """Return the path to a qc metrics deliverables file with case data."""
    return Path(apps_dir, "raredisease", "case_metrics_deliverables.yaml")


@pytest.fixture
def mip_analysis_dir(analysis_dir: Path) -> Path:
    """Return the path to the directory with mip analysis files."""
    return Path(analysis_dir, "mip")


@pytest.fixture
def balsamic_analysis_dir(analysis_dir: Path) -> Path:
    """Return the path to the directory with balsamic analysis files."""
    return Path(analysis_dir, "balsamic")


@pytest.fixture
def balsamic_wgs_analysis_dir(balsamic_analysis_dir: Path) -> Path:
    """Return the path to the directory with balsamic analysis files."""
    return Path(balsamic_analysis_dir, "tn_wgs")


@pytest.fixture
def mip_dna_analysis_dir(mip_analysis_dir: Path) -> Path:
    """Return the path to the directory with mip dna analysis files."""
    return Path(mip_analysis_dir, "dna")


@pytest.fixture
def nf_analysis_analysis_dir(fixtures_dir: Path) -> Path:
    """Return the path to the directory with nf-analysis files."""
    return Path(fixtures_dir, "analysis", "nf-analysis")


@pytest.fixture
def raredisease_analysis_dir(analysis_dir: Path) -> Path:
    """Return the path to the directory with raredisease analysis files."""
    return Path(analysis_dir, "raredisease")


@pytest.fixture
def rnafusion_analysis_dir(analysis_dir: Path) -> Path:
    """Return the path to the directory with rnafusion analysis files."""
    return Path(analysis_dir, "rnafusion")


@pytest.fixture
def taxprofiler_analysis_dir(analysis_dir: Path) -> Path:
    """Return the path to the directory with taxprofiler analysis files."""
    return Path(analysis_dir, "taxprofiler")


@pytest.fixture
def sample_cram(mip_dna_analysis_dir: Path) -> Path:
    """Return the path to the cram file for a sample."""
    return Path(mip_dna_analysis_dir, "adm1.cram")


@pytest.fixture(name="father_sample_cram")
def father_sample_cram(
    mip_dna_analysis_dir: Path,
    father_sample_id: str,
) -> Path:
    """Return the path to the cram file for the father sample."""
    return Path(mip_dna_analysis_dir, father_sample_id + FileExtensions.CRAM)


@pytest.fixture(name="mother_sample_cram")
def mother_sample_cram(mip_dna_analysis_dir: Path, mother_sample_id: str) -> Path:
    """Return the path to the cram file for the mother sample."""
    return Path(mip_dna_analysis_dir, mother_sample_id + FileExtensions.CRAM)


@pytest.fixture(name="sample_cram_files")
def sample_crams(
    sample_cram: Path, father_sample_cram: Path, mother_sample_cram: Path
) -> list[Path]:
    """Return a list of cram paths for three samples."""
    return [sample_cram, father_sample_cram, mother_sample_cram]


@pytest.fixture(name="vcf_file")
def vcf_file(mip_dna_store_files: Path) -> Path:
    """Return the path to a VCF file."""
    return Path(mip_dna_store_files, "yellowhog_clinical_selected.vcf")


@pytest.fixture(name="madeline_output")
def madeline_output(apps_dir: Path) -> Path:
    """Return str of path for file with Madeline output."""
    return Path(apps_dir, "madeline", "madeline.xml")


@pytest.fixture(name="file_does_not_exist")
def file_does_not_exist() -> Path:
    """Return a file path that does not exist."""
    return Path("file", "does", "not", "exist")


# Compression fixtures


@pytest.fixture(name="run_name")
def run_name() -> str:
    """Return the name of a fastq run."""
    return "fastq_run"


@pytest.fixture(name="original_fastq_data")
def original_fastq_data(fastq_dir: Path, run_name) -> CompressionData:
    """Return a compression object with a path to the original fastq files."""
    return CompressionData(Path(fastq_dir, run_name))


@pytest.fixture(name="fastq_stub")
def fastq_stub(project_dir: Path, run_name: str) -> Path:
    """Creates a path to the base format of a fastq run."""
    return Path(project_dir, run_name)


@pytest.fixture(name="compression_object")
def compression_object(fastq_stub: Path, original_fastq_data: CompressionData) -> CompressionData:
    """Creates compression data object with information about files used in fastq compression."""
    working_files: CompressionData = CompressionData(fastq_stub)
    working_file_map: dict[str, str] = {
        original_fastq_data.fastq_first.as_posix(): working_files.fastq_first.as_posix(),
        original_fastq_data.fastq_second.as_posix(): working_files.fastq_second.as_posix(),
    }
    for original_file, working_file in working_file_map.items():
        shutil.copy(original_file, working_file)
    return working_files


# Genotype file fixture


@pytest.fixture(name="bcf_file")
def bcf_file(apps_dir: Path) -> Path:
    """Return the path to a BCF file."""
    return Path(apps_dir, "gt", "yellowhog.bcf")


# Gens file fixtures


@pytest.fixture(name="gens_fracsnp_path")
def gens_fracsnp_path(mip_dna_analysis_dir: Path, sample_id: str) -> Path:
    """Path to Gens fracsnp/baf bed file."""
    return Path(mip_dna_analysis_dir, f"{sample_id}.baf.bed.gz")


@pytest.fixture(name="gens_coverage_path")
def gens_coverage_path(mip_dna_analysis_dir: Path, sample_id: str) -> Path:
    """Path to Gens coverage bed file."""
    return Path(mip_dna_analysis_dir, f"{sample_id}.cov.bed.gz")


# Housekeeper, Chanjo file fixtures


@pytest.fixture(name="bed_file")
def bed_file(analysis_dir) -> Path:
    """Return the path to a bed file."""
    return Path(analysis_dir, "sample_coverage.bed")


# Helper fixtures


@pytest.fixture(scope="session")
def helpers() -> StoreHelpers:
    """Return a class with helper functions for the stores."""
    return StoreHelpers()


@pytest.fixture(name="small_helpers")
def small_helpers() -> SmallHelpers:
    """Return a class with small helper functions."""
    return SmallHelpers()


# HK fixtures


@pytest.fixture(name="root_path")
def root_path(project_dir: Path) -> Path:
    """Return the path to a hk bundles dir."""
    _root_path = Path(project_dir, "bundles")
    _root_path.mkdir(parents=True, exist_ok=True)
    return _root_path


@pytest.fixture(name="hk_bundle_sample_path")
def hk_bundle_sample_path(sample_id: str, timestamp: datetime) -> Path:
    """Return the relative path to a Housekeeper bundle mock sample."""
    return Path(sample_id, timestamp.strftime("%Y-%m-%d"))


@pytest.fixture(name="hk_bundle_data")
def hk_bundle_data(
    case_id: str,
    bed_file: Path,
    delivery_report_html: Path,
    timestamp_yesterday: datetime,
    sample_id: str,
    father_sample_id: str,
    mother_sample_id: str,
) -> dict[str, Any]:
    """Return some bundle data for Housekeeper."""
    return {
        "name": case_id,
        "created": timestamp_yesterday,
        "expires": timestamp_yesterday,
        "files": [
            {
                "path": bed_file.as_posix(),
                "archive": False,
                "tags": ["bed", sample_id, father_sample_id, mother_sample_id, "coverage"],
            },
            {
                "path": delivery_report_html.as_posix(),
                "archive": False,
                "tags": [HK_DELIVERY_REPORT_TAG],
            },
        ],
    }


@pytest.fixture(name="hk_sample_bundle")
def hk_sample_bundle(
    fastq_file: Path,
    sample_hk_bundle_no_files: dict,
    sample_id: str,
    spring_file: Path,
) -> dict:
    """Returns a dict for building a housekeeper bundle for a sample."""
    sample_hk_bundle_no_files["files"] = [
        {
            "path": spring_file.as_posix(),
            "archive": False,
            "tags": [SequencingFileTag.SPRING, sample_id],
        },
        {
            "path": fastq_file.as_posix(),
            "archive": False,
            "tags": [SequencingFileTag.FASTQ, sample_id],
        },
    ]
    return sample_hk_bundle_no_files


@pytest.fixture(name="hk_father_sample_bundle")
def hk_father_sample_bundle(
    fastq_file_father: Path,
    helpers,
    sample_hk_bundle_no_files: dict,
    father_sample_id: str,
    spring_file_father: Path,
) -> dict:
    """Returns a dict for building a housekeeper bundle for a second sample."""
    father_sample_bundle = deepcopy(sample_hk_bundle_no_files)
    father_sample_bundle["name"] = father_sample_id
    father_sample_bundle["files"] = [
        {
            "path": spring_file_father.as_posix(),
            "archive": False,
            "tags": [SequencingFileTag.SPRING, father_sample_id],
        },
        {
            "path": fastq_file_father.as_posix(),
            "archive": False,
            "tags": [SequencingFileTag.FASTQ, father_sample_id],
        },
    ]
    return father_sample_bundle


@pytest.fixture(name="sample_hk_bundle_no_files")
def sample_hk_bundle_no_files(sample_id: str, timestamp: datetime) -> dict:
    """Create a complete bundle mock for testing compression."""
    return {
        "name": sample_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [],
    }


@pytest.fixture(name="case_hk_bundle_no_files")
def case_hk_bundle_no_files(case_id: str, timestamp: datetime) -> dict:
    """Create a complete bundle mock for testing compression."""
    return {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [],
    }


@pytest.fixture(name="compress_hk_fastq_bundle")
def compress_hk_fastq_bundle(
    compression_object: CompressionData, sample_hk_bundle_no_files: dict
) -> dict:
    """Create a complete bundle mock for testing compression
    This bundle contains a pair of fastq files.
    ."""
    hk_bundle_data = deepcopy(sample_hk_bundle_no_files)

    first_fastq = compression_object.fastq_first
    second_fastq = compression_object.fastq_second
    for fastq_file in [first_fastq, second_fastq]:
        fastq_file.touch()
        # We need to set the time to an old date
        # Create an older date
        # Convert the date to a float
        before_timestamp = datetime.timestamp(datetime(2020, 1, 1))
        # Update the utime so file looks old
        os.utime(fastq_file, (before_timestamp, before_timestamp))
        fastq_file_info = {
            "path": str(fastq_file),
            "archive": False,
            "tags": [SequencingFileTag.FASTQ],
        }

        hk_bundle_data["files"].append(fastq_file_info)
    return hk_bundle_data


@pytest.fixture(name="housekeeper_api")
def housekeeper_api(hk_config_dict: dict) -> MockHousekeeperAPI:
    """Setup Housekeeper store."""
    return MockHousekeeperAPI(hk_config_dict)


@pytest.fixture(name="real_housekeeper_api")
def real_housekeeper_api(hk_config_dict: dict) -> Generator[HousekeeperAPI, None, None]:
    """Set up a real Housekeeper store."""
    _api = HousekeeperAPI(hk_config_dict)
    _api.initialise_db()
    yield _api


@pytest.fixture(name="populated_housekeeper_api")
def populated_housekeeper_api(
    real_housekeeper_api: HousekeeperAPI,
    hk_bundle_data: dict,
    hk_father_sample_bundle: dict,
    hk_sample_bundle: dict,
    helpers,
) -> HousekeeperAPI:
    """Setup a Housekeeper store with some data."""
    hk_api = real_housekeeper_api
    helpers.ensure_hk_bundle(store=hk_api, bundle_data=hk_bundle_data)
    helpers.ensure_hk_bundle(store=hk_api, bundle_data=hk_sample_bundle)
    helpers.ensure_hk_bundle(store=hk_api, bundle_data=hk_father_sample_bundle)
    return hk_api


@pytest.fixture(name="hk_version")
def hk_version(housekeeper_api: MockHousekeeperAPI, hk_bundle_data: dict, helpers) -> Version:
    """Get a Housekeeper version object."""
    return helpers.ensure_hk_version(housekeeper_api, hk_bundle_data)


# Process Mock


@pytest.fixture(name="process")
def process() -> ProcessMock:
    """Returns a mocked process."""
    return ProcessMock()


# Hermes mock


@pytest.fixture(name="hermes_process")
def hermes_process() -> ProcessMock:
    """Return a mocked Hermes process."""
    return ProcessMock(binary="hermes")


@pytest.fixture(name="hermes_api")
def hermes_api(hermes_process: ProcessMock) -> HermesApi:
    """Return a Hermes API with a mocked process."""
    hermes_config = {"hermes": {"binary_path": "/bin/true"}}
    hermes_api = HermesApi(config=hermes_config)
    hermes_api.process = hermes_process
    return hermes_api


# Scout fixtures


@pytest.fixture(name="scout_api")
def scout_api() -> MockScoutAPI:
    """Setup Scout API."""
    return MockScoutAPI()


# Crunchy fixtures


@pytest.fixture(name="crunchy_api")
def crunchy_api():
    """Setup Crunchy API."""
    return MockCrunchyAPI()


# Store fixtures


@pytest.fixture(name="analysis_store")
def analysis_store(
    base_store: Store,
    analysis_family: dict,
    wgs_application_tag: str,
    helpers: StoreHelpers,
    timestamp_yesterday: datetime,
) -> Generator[Store, None, None]:
    """Set up a store instance for testing analysis API."""
    helpers.ensure_case_from_dict(
        base_store,
        case_info=analysis_family,
        app_tag=wgs_application_tag,
        started_at=timestamp_yesterday,
    )
    yield base_store


@pytest.fixture(name="analysis_store_trio")
def analysis_store_trio(analysis_store: Store) -> Generator[Store, None, None]:
    """Setup a store instance with a trio loaded for testing analysis API."""
    yield analysis_store


@pytest.fixture
def analysis_store_single_case(
    base_store: Store, analysis_family_single_case: Store, helpers: StoreHelpers
):
    """Set up a store instance with a single ind case for testing analysis API."""
    helpers.ensure_case_from_dict(base_store, case_info=analysis_family_single_case)
    yield base_store


@pytest.fixture
def store_with_illumina_sequencing_data(
    store: Store,
    helpers: StoreHelpers,
    seven_canonical_flow_cells: list[IlluminaRunDirectoryData],
    seven_canonical_flow_cells_selected_sample_ids: list[list[str]],
    seven_canonical_sequencing_runs_selected_case_ids: list[list[str]],
) -> Store:
    """Return a store with Illumina flow cells, sequencing runs and sample sequencing metrics."""
    for run_dir, sample_internal_ids, case_ids in zip(
        seven_canonical_flow_cells,
        seven_canonical_flow_cells_selected_sample_ids,
        seven_canonical_sequencing_runs_selected_case_ids,
    ):
        helpers.add_illumina_flow_cell_and_samples_with_sequencing_metrics(
            run_directory_data=run_dir,
            sample_ids=sample_internal_ids,
            case_ids=case_ids,
            store=store,
        )
    return store


@pytest.fixture
def store_with_illumina_sequencing_data_on_disk(
    store_with_illumina_sequencing_data: Store,
    selected_novaseq_x_case_ids: list[str],
    helpers: StoreHelpers,
    novaseq_6000_pre_1_5_kits_flow_cell_id: str,
    novaseq_6000_pre_1_5_kits_flow_cell: IlluminaRunDirectoryData,
    selected_novaseq_6000_pre_1_5_kits_sample_ids: list[str],
) -> Store:
    """Store with illumina sequencing data for run on disk tests."""
    store_with_illumina_sequencing_data.delete_illumina_flow_cell(
        novaseq_6000_pre_1_5_kits_flow_cell_id
    )
    helpers.add_illumina_flow_cell_and_samples_with_sequencing_metrics(
        run_directory_data=novaseq_6000_pre_1_5_kits_flow_cell,
        sample_ids=[selected_novaseq_6000_pre_1_5_kits_sample_ids[0]],
        case_ids=[selected_novaseq_x_case_ids[0]],
        store=store_with_illumina_sequencing_data,
    )
    return store_with_illumina_sequencing_data


@pytest.fixture
def re_sequenced_sample_illumina_data_store(
    store_with_illumina_sequencing_data: Store,
    sample_id_sequenced_on_multiple_flow_cells: str,
    flow_cells_with_the_same_sample: list[str],
    case_id_for_sample_on_multiple_flow_cells: str,
    helpers: StoreHelpers,
) -> Store:
    """Return a store with re-sequenced samples on illumina flow cells for Fluffy case."""
    sequencing_run: IlluminaSequencingRun = (
        store_with_illumina_sequencing_data.get_illumina_sequencing_run_by_device_internal_id(
            flow_cells_with_the_same_sample[1]
        )
    )
    helpers.add_illumina_sample_sequencing_metrics_object(
        store=store_with_illumina_sequencing_data,
        sample_id=sample_id_sequenced_on_multiple_flow_cells,
        sequencing_run=sequencing_run,
        lane=1,
    )
    # Add application and tags to case
    application: Application = helpers.ensure_application(
        store=store_with_illumina_sequencing_data, tag="RMLO05R800", prep_category="rml"
    )
    application_version: ApplicationVersion = helpers.ensure_application_version(
        store=store_with_illumina_sequencing_data, tag="RMLO05R800", prep_category="rml"
    )
    case: Case = store_with_illumina_sequencing_data.get_case_by_internal_id(
        case_id_for_sample_on_multiple_flow_cells
    )
    case.data_analysis = Workflow.FLUFFY
    case.links[0].sample.application_version = application_version
    case.links[0].sample.application_version.application = application
    return store_with_illumina_sequencing_data


@pytest.fixture
def collaboration_id() -> str:
    """Return a default customer group."""
    return "hospital_collaboration"


@pytest.fixture
def mip_dna_loqusdb_customer(collaboration_id: str, customer_id: str) -> Customer:
    """Return a Rare Disease customer."""
    return Customer(
        name="Klinisk Immunologi",
        internal_id=CustomerId.CUST004,
        loqus_upload=True,
    )


@pytest.fixture
def balsamic_loqusdb_customer(collaboration_id: str, customer_id: str) -> Customer:
    """Return a Cancer customer."""
    return Customer(
        name="AML",
        internal_id=CustomerId.CUST110,
        loqus_upload=True,
    )


@pytest.fixture
def raredisease_loqusdb_customer(collaboration_id: str, customer_id: str) -> Customer:
    """Return a customer with enabled observation upload."""
    return Customer(
        name="Klinisk Immunologi",
        internal_id=CustomerId.CUST004,
        loqus_upload=True,
    )


@pytest.fixture
def external_wes_application_tag() -> str:
    """Return the external whole exome sequencing application tag."""
    return "EXXCUSR000"


@pytest.fixture
def wgs_application_tag() -> str:
    """Return the WGS application tag."""
    return "WGSPCFC030"


@pytest.fixture
def wts_application_tag() -> str:
    """Return a WTS application tag."""
    return "RNAPOAR100"


@pytest.fixture
def microbial_application_tag() -> str:
    """Return the WGS microbial application tag."""
    return "MWRNXTR003"


@pytest.fixture
def metagenomics_application_tag() -> str:
    """Return the metagenomics application tag."""
    return "METPCFR030"


@pytest.fixture
def store() -> Generator[Store, None, None]:
    """Return a CG store."""
    initialize_database("sqlite:///")
    _store = Store()
    create_all_tables()
    yield _store
    drop_all_tables()


@pytest.fixture
def apptag_rna() -> str:
    """Return the RNA application tag."""
    return "RNAPOAR025"


@pytest.fixture
def bed_name() -> str:
    """Return a bed model name attribute."""
    return "Bed"


@pytest.fixture
def bed_version_file_name(bed_name: str) -> str:
    """Return a bed version model file name attribute."""
    return f"{bed_name}.bed"


@pytest.fixture
def bed_version_short_name() -> str:
    """Return a bed version model short name attribute."""
    return "bed_short_name_0.0"


@pytest.fixture
def invoice_address() -> str:
    """Return an invoice address."""
    return "Test street"


@pytest.fixture
def invoice_reference() -> str:
    """Return an invoice reference."""
    return "ABCDEF"


@pytest.fixture
def prices() -> dict[str, int]:
    """Return dictionary with prices for each priority status."""
    return {"standard": 10, "priority": 20, "express": 30, "research": 5}


@pytest.fixture
def base_store(
    apptag_rna: str,
    bed_name: str,
    bed_version_short_name: str,
    collaboration_id: str,
    customer_id: str,
    invoice_address: str,
    invoice_reference: str,
    store: Store,
    prices: dict[str, int],
) -> Generator[Store, None, None]:
    """Setup and example store."""
    collaboration = store.add_collaboration(internal_id=collaboration_id, name=collaboration_id)

    store.session.add(collaboration)
    customers: list[Customer] = []
    customer_map: dict[str, str] = {
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

    beds: list[Bed] = [store.add_bed(name=bed_name)]
    store.session.add_all(beds)
    bed_versions: list[BedVersion] = [
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


@pytest.fixture
def sample_store(base_store: Store) -> Store:
    """Populate store with samples."""
    new_samples = [
        base_store.add_sample(name="ordered", sex=Sex.MALE, internal_id="test_internal_id"),
        base_store.add_sample(name="received", sex=Sex.UNKNOWN, received=datetime.now()),
        base_store.add_sample(
            name="received-prepared",
            sex=Sex.UNKNOWN,
            received=datetime.now(),
            prepared_at=datetime.now(),
        ),
        base_store.add_sample(name="external", sex=Sex.FEMALE),
        base_store.add_sample(name="external-received", sex=Sex.FEMALE, received=datetime.now()),
        base_store.add_sample(
            name="sequenced",
            sex=Sex.MALE,
            received=datetime.now(),
            prepared_at=datetime.now(),
            last_sequenced_at=datetime.now(),
            reads=(310 * 1000000),
        ),
        base_store.add_sample(
            name="sequenced-partly",
            sex=Sex.MALE,
            received=datetime.now(),
            prepared_at=datetime.now(),
            reads=(250 * 1000000),
        ),
        base_store.add_sample(
            name="to-deliver",
            sex=Sex.MALE,
            last_sequenced_at=datetime.now(),
        ),
        base_store.add_sample(
            name="delivered",
            sex=Sex.MALE,
            last_sequenced_at=datetime.now(),
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


@pytest.fixture(scope="session")
def trailblazer_api() -> MockTB:
    """Return a mock Trailblazer API."""
    return MockTB()


@pytest.fixture(scope="session")
def lims_api() -> MockLimsAPI:
    """Return a mock LIMS API."""
    return MockLimsAPI()


@pytest.fixture
def lims_api_with_sample_and_internal_negative_control(lims_api: MockLimsAPI) -> MockLimsAPI:
    sample_qc_pass = LimsSample(id="sample", name="sample")

    internal_negative_control_qc_pass = LimsSample(
        id="internal_negative_control",
        name="internal_negative_control",
        udfs=LimsUDF(control="negative", customer="cust000"),
    )

    # Create pools
    samples_qc_pass = [
        sample_qc_pass,
        internal_negative_control_qc_pass,
    ]
    # Add pool artifacts
    lims_api.add_artifact_for_sample(sample_id=sample_qc_pass.id, samples=samples_qc_pass)

    return lims_api


@pytest.fixture(scope="session")
def config_root_dir() -> Path:
    """Return a path to the config root directory."""
    return Path("tests", "fixtures", "data")


@pytest.fixture(scope="session")
def housekeeper_dir(tmpdir_factory):
    """Return a temporary directory for Housekeeper testing."""
    return tmpdir_factory.mktemp("housekeeper")


@pytest.fixture(scope="session")
def mip_dir(tmpdir_factory) -> Path:
    """Return a temporary directory for MIP testing."""
    return tmpdir_factory.mktemp("mip")


@pytest.fixture(scope="session")
def fluffy_dir(tmpdir_factory) -> Path:
    """Return a temporary directory for Fluffy testing."""
    return tmpdir_factory.mktemp("fluffy")


@pytest.fixture(scope="session")
def balsamic_dir(tmpdir_factory) -> Path:
    """Return a temporary directory for Balsamic testing."""
    return tmpdir_factory.mktemp("balsamic")


@pytest.fixture(scope="session")
def cg_dir(tmpdir_factory) -> Path:
    """Return a temporary directory for cg testing."""
    return tmpdir_factory.mktemp("cg")


@pytest.fixture(scope="function")
def downsample_dir(tmp_path_factory) -> Path:
    """Return a temporary downsample directory for testing."""
    return tmp_path_factory.mktemp("downsample", numbered=True)


@pytest.fixture(name="swegen_dir")
def swegen_dir(tmpdir_factory, tmp_path) -> Path:
    """SweGen temporary directory containing mocked reference files."""
    return tmpdir_factory.mktemp("swegen")


@pytest.fixture(name="swegen_snv_reference")
def swegen_snv_reference_path(swegen_dir: Path) -> Path:
    """Return a temporary path to a SweGen SNV reference file."""
    mock_file = Path(swegen_dir, "grch37_swegen_10k_snv_-20220101-.vcf.gz")
    mock_file.touch(exist_ok=True)
    return mock_file


@pytest.fixture(name="observations_dir")
def observations_dir(tmpdir_factory, tmp_path) -> Path:
    """Loqusdb temporary directory containing observations mock files."""
    return tmpdir_factory.mktemp("loqusdb")


@pytest.fixture(name="observations_clinical_snv_file_path")
def observations_clinical_snv_file_path(observations_dir: Path) -> Path:
    """Return a temporary path to a clinical SNV file."""
    mock_file = Path(observations_dir, "loqusdb_clinical_snv_export-20220101-.vcf.gz")
    mock_file.touch(exist_ok=True)
    return mock_file


@pytest.fixture(name="observations_clinical_sv_file_path")
def observations_clinical_sv_file_path(observations_dir: Path) -> Path:
    """Return a temporary path to a clinical SV file."""
    mock_file = Path(observations_dir, "loqusdb_clinical_sv_export-20220101-.vcf.gz")
    mock_file.touch(exist_ok=True)
    return mock_file


@pytest.fixture(name="observations_somatic_snv_file_path")
def observations_somatic_snv_file_path(observations_dir: Path) -> Path:
    """Return a temporary path to a cancer somatic SNV file."""
    mock_file = Path(observations_dir, "loqusdb_cancer_somatic_snv_export-20220101-.vcf.gz")
    mock_file.touch(exist_ok=True)
    return mock_file


@pytest.fixture(name="outdated_observations_somatic_snv_file_path")
def outdated_observations_somatic_snv_file_path(observations_dir: Path) -> Path:
    """Return a temporary path to an outdated cancer somatic SNV file."""
    mock_file = Path(observations_dir, "loqusdb_cancer_somatic_snv_export-20180101-.vcf.gz")
    mock_file.touch(exist_ok=True)
    return mock_file


@pytest.fixture(name="custom_observations_clinical_snv_file_path")
def custom_observations_clinical_snv_file_path(observations_dir: Path) -> Path:
    """Return a custom path for the clinical SNV observations file."""
    return Path(observations_dir, "clinical_snv_export-19990101-.vcf.gz")


@pytest.fixture(scope="session")
def microsalt_dir(tmpdir_factory) -> Path:
    """Return a temporary directory for Microsalt testing."""
    return tmpdir_factory.mktemp("microsalt")


@pytest.fixture
def pdc_archiving_dir(tmp_flow_cell_without_run_parameters_path: Path) -> Path:
    """Return a temporary directory for PDC archiving testing."""
    return tmp_flow_cell_without_run_parameters_path


@pytest.fixture
def pdc_archiving_directory(pdc_archiving_dir: Path) -> PDCArchivingDirectory:
    """Returns different PDC archiving directories."""
    return PDCArchivingDirectory(
        current=f"/{pdc_archiving_dir.as_posix()}/", nas="/ENCRYPT/", pre_nas="/OLD_ENCRYPT/"
    )


@pytest.fixture(scope="function")
def nextflow_binary() -> Path:
    """Return the path to the nextflow binary."""
    return Path("path", "to", "bin", "nextflow")


@pytest.fixture(scope="function")
def conda_binary() -> Path:
    """Return the path to the conda binary."""
    return Path("path", "to", "bin", "conda")


@pytest.fixture(name="cg_uri")
def cg_uri() -> str:
    """Return a cg URI."""
    return "sqlite:///"


@pytest.fixture(name="hk_uri")
def hk_uri() -> str:
    """Return a Housekeeper URI."""
    return "sqlite:///"


@pytest.fixture(name="context_config")
def context_config(
    cg_uri: str,
    hk_uri: str,
    email_address: str,
    fluffy_dir: Path,
    housekeeper_dir: Path,
    mip_dir: Path,
    cg_dir: Path,
    conda_binary: Path,
    balsamic_dir: Path,
    microsalt_dir: Path,
    raredisease_dir: Path,
    rnafusion_dir: Path,
    taxprofiler_dir: Path,
    tomte_dir: Path,
    illumina_sequencing_runs_directory: Path,
    illumina_demultiplexed_runs_directory: Path,
    downsample_dir: Path,
    pdc_archiving_directory: PDCArchivingDirectory,
    nextflow_binary: Path,
    nf_analysis_platform_config_path: Path,
    nf_analysis_pipeline_params_path: Path,
    nf_analysis_pipeline_resource_optimisation_path: Path,
) -> dict:
    """Return a context config."""
    return {
        "database": cg_uri,
        "delivery_path": str(cg_dir),
        "nanopore_data_directory": "path/to/nanopore_data_directory",
        "run_instruments": {
            "pacbio": {
                "data_dir": "path/to/pacbio_data__directory",
                "systemd_trigger_dir": "path/to/pacbio_trigger_directory",
            },
            "nanopore": {
                "data_dir": "path/to/nanopore_data_directory",
                "systemd_trigger_dir": "path/to/nanopore_trigger_directory",
            },
            "illumina": {
                "sequencing_runs_dir": str(illumina_sequencing_runs_directory),
                "demultiplexed_runs_dir": str(illumina_demultiplexed_runs_directory),
            },
        },
        "downsample": {
            "downsample_dir": str(downsample_dir),
            "downsample_script": "downsample.sh",
            "account": "development",
        },
        "email_base_settings": {
            "sll_port": 465,
            "smtp_server": "smtp.gmail.com",
            "sender_email": "test@gmail.com",
            "sender_password": "",
        },
        "madeline_exe": "echo",
        "sentieon_licence_server": "127.0.0.1:8080",
        "tower_binary_path": Path("path", "to", "bin", "tw").as_posix(),
        "pon_path": str(cg_dir),
        "illumina_backup_service": {
            "pdc_archiving_directory": pdc_archiving_directory.dict(),
            "slurm_flow_cell_encryption": {
                "account": "development",
                "hours": 1,
                "mail_user": email_address,
                "memory": 1,
                "number_tasks": 1,
            },
        },
        "balsamic": {
            "balsamic_cache": "hello",
            "bed_path": str(cg_dir),
            "binary_path": "echo",
            "cadd_path": str(cg_dir),
            "conda_binary": "a_conda_binary",
            "conda_env": "S_balsamic",
            "genome_interval_path": str(cg_dir),
            "gens_coverage_female_path": str(cg_dir),
            "gens_coverage_male_path": str(cg_dir),
            "gnomad_af5_path": str(cg_dir),
            "loqusdb_path": str(cg_dir),
            "pon_path": str(cg_dir),
            "root": str(balsamic_dir),
            "slurm": {
                "account": "development",
                "mail_user": email_address,
                "qos": SlurmQos.LOW,
            },
            "sentieon_licence_path": str(cg_dir),
            "swegen_path": str(cg_dir),
        },
        "chanjo": {"binary_path": "echo", "config_path": "chanjo-stage.yaml"},
        "chanjo2": {"host": "chanjo2_host"},
        "crunchy": {
            "conda_binary": "a_conda_binary",
            "cram_reference": "grch37_homo_sapiens_-d5-.fasta",
            "slurm": {
                "account": "development",
                "conda_env": "S_crunchy",
                "hours": 1,
                "mail_user": email_address,
                "memory": 1,
                "number_tasks": 1,
            },
        },
        "data-delivery": {
            "account": "development",
            "base_path": "/another/path",
            "covid_destination_path": "server.name.se:/another/%s/foldername/",
            "covid_source_path": "a/source/path",
            "covid_report_path": "/folder_structure/%s/yet_another_folder/filename_%s_data_*.csv",
            "destination_path": "server.name.se:/some",
            "mail_user": email_address,
        },
        "data_input": {"input_dir_path": str(cg_dir)},
        "demultiplex": {
            "run_dir": "tests/fixtures/apps/demultiplexing/sequencing-runs/nova_seq_6000",
            "out_dir": "tests/fixtures/apps/demultiplexing/demultiplexed-runs",
            "slurm": {
                "account": "development",
                "mail_user": email_address,
            },
        },
        "encryption": {
            "binary_path": "bin/gpg",
            "encryption_dir": pdc_archiving_directory.current,
        },
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
        "loqusdb": {"binary_path": "loqusdb", "config_path": "loqusdb.yaml"},
        "loqusdb-wes": {"binary_path": "loqusdb-wes", "config_path": "loqusdb-wes.yaml"},
        "loqusdb-somatic": {
            "binary_path": "loqusdb-somatic",
            "config_path": "loqusdb-somatic.yaml",
        },
        "loqusdb-tumor": {"binary_path": "loqusdb-tumor", "config_path": "loqusdb-tumor.yaml"},
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
            "workflow": "analyse rd_dna",
            "root": str(mip_dir),
            "script": "mip",
        },
        "mip-rd-rna": {
            "conda_binary": "a_conda_binary",
            "conda_env": "S_mip9.0",
            "mip_config": "mip9.0-rna-stage.yaml",
            "workflow": "analyse rd_rna",
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
        "raredisease": {
            "binary_path": nextflow_binary.as_posix(),
            "compute_env": "nf_tower_compute_env",
            "conda_binary": conda_binary.as_posix(),
            "conda_env": "S_raredisease",
            "config_platform": str(nf_analysis_platform_config_path),
            "config_params": str(nf_analysis_pipeline_params_path),
            "config_resources": str(nf_analysis_pipeline_resource_optimisation_path),
            "launch_directory": Path("path", "to", "launchdir").as_posix(),
            "workflow_path": Path("workflow", "path").as_posix(),
            "profile": "myprofile",
            "references": Path("path", "to", "references").as_posix(),
            "revision": "2.2.0",
            "root": str(raredisease_dir),
            "slurm": {
                "account": "development",
                "mail_user": email_address,
            },
            "tower_workflow": "raredisease",
        },
        "tomte": {
            "binary_path": nextflow_binary.as_posix(),
            "compute_env": "nf_tower_compute_env",
            "conda_binary": conda_binary.as_posix(),
            "conda_env": "S_tomte",
            "config_platform": str(nf_analysis_platform_config_path),
            "config_params": str(nf_analysis_pipeline_params_path),
            "config_resources": str(nf_analysis_pipeline_resource_optimisation_path),
            "workflow_path": Path("workflow", "path").as_posix(),
            "profile": "myprofile",
            "references": Path("path", "to", "references").as_posix(),
            "revision": "2.2.0",
            "root": str(tomte_dir),
            "slurm": {
                "account": "development",
                "mail_user": email_address,
            },
            "tower_workflow": "tomte",
        },
        "rnafusion": {
            "binary_path": nextflow_binary.as_posix(),
            "compute_env": "nf_tower_compute_env",
            "conda_binary": conda_binary.as_posix(),
            "conda_env": "S_RNAFUSION",
            "launch_directory": Path("path", "to", "launchdir").as_posix(),
            "workflow_path": Path("workflow", "path").as_posix(),
            "profile": "myprofile",
            "references": Path("path", "to", "references").as_posix(),
            "revision": "2.2.0",
            "root": str(rnafusion_dir),
            "slurm": {
                "account": "development",
                "mail_user": "test.rnafusion.email@scilifelab.se",
            },
            "tower_workflow": "rnafusion",
        },
        "pigz": {"binary_path": "/bin/pigz"},
        "pdc": {"binary_path": "/bin/dsmc"},
        "taxprofiler": {
            "binary_path": nextflow_binary.as_posix(),
            "compute_env": "nf_tower_compute_env",
            "root": str(taxprofiler_dir),
            "conda_binary": conda_binary.as_posix(),
            "conda_env": "S_taxprofiler",
            "launch_directory": Path("path", "to", "launchdir").as_posix(),
            "workflow_path": Path("workflow", "path").as_posix(),
            "databases": Path("path", "to", "databases").as_posix(),
            "profile": "myprofile",
            "hostremoval_reference": Path("path", "to", "hostremoval_reference").as_posix(),
            "revision": "2.2.0",
            "slurm": {
                "account": "development",
                "mail_user": "taxprofiler.email@scilifelab.se",
            },
            "tower_workflow": "taxprofiler",
        },
        "scout": {
            "binary_path": "bin/scout",
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
        "arnold": {"api_url": "https://arnold.scilifelab.se/"},
        "janus": {"host": "https://janus.sys.scilifelab.se/"},
    }


@pytest.fixture(name="cg_context")
def cg_context(
    context_config: dict, base_store: Store, housekeeper_api: MockHousekeeperAPI
) -> CGConfig:
    """Return a cg config."""
    cg_config = CGConfig(**context_config)
    cg_config.status_db_ = base_store
    cg_config.housekeeper_api_ = housekeeper_api
    return cg_config


@pytest.fixture
def context_with_illumina_data(
    context_config: dict, store_with_illumina_sequencing_data, housekeeper_api: MockHousekeeperAPI
) -> CGConfig:
    cg_config = CGConfig(**context_config)
    cg_config.status_db_ = store_with_illumina_sequencing_data
    cg_config.housekeeper_api_ = housekeeper_api
    return cg_config


@pytest.fixture(scope="session")
def case_id_with_single_sample() -> str:
    """Return a case id that should only be associated with one sample."""
    return "exhaustedcrocodile"


@pytest.fixture(scope="session")
def case_id_with_multiple_samples() -> str:
    """Return a case id that should be associated with multiple samples."""
    return "righteouspanda"


@pytest.fixture(scope="session")
def case_id_without_samples() -> str:
    """Return a case id that should not be associated with any samples."""
    return "confusedtrout"


@pytest.fixture(scope="session")
def case_id_not_enough_reads() -> str:
    """Return a case id associated to a sample without enough reads."""
    return "tiredwalrus"


@pytest.fixture(scope="session")
def sample_id_in_single_case() -> str:
    """Return a sample id that should be associated with a single case."""
    return "ASM1"


@pytest.fixture(scope="session")
def sample_id_in_multiple_cases() -> str:
    """Return a sample id that should be associated with multiple cases."""
    return "ASM2"


@pytest.fixture(scope="session")
def sample_id_not_enough_reads() -> str:
    """Return a sample id without enough reads."""
    return "ASM3"


@pytest.fixture(name="store_with_multiple_cases_and_samples")
def store_with_multiple_cases_and_samples(
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

    case_samples: list[tuple[str, str]] = [
        (case_id_with_multiple_samples, sample_id_in_multiple_cases),
        (case_id, sample_id_in_multiple_cases),
        (case_id_with_single_sample, sample_id_in_single_case),
    ]

    for case_sample in case_samples:
        case_id, sample_id = case_sample
        helpers.add_case_with_sample(base_store=store, case_id=case_id, sample_id=sample_id)

    yield store


@pytest.fixture(name="store_with_panels")
def store_with_panels(store: Store, helpers: StoreHelpers):
    helpers.ensure_panel(store=store, panel_abbreviation="panel1", customer_id="cust000")
    helpers.ensure_panel(store=store, panel_abbreviation="panel2", customer_id="cust000")
    helpers.ensure_panel(store=store, panel_abbreviation="panel3", customer_id="cust000")
    yield store


@pytest.fixture
def store_with_organisms(store: Store, helpers: StoreHelpers) -> Generator[Store, None, None]:
    """Return a store with multiple organisms."""

    organism_details = [
        ("organism_1", "Organism 1"),
        ("organism_2", "Organism 2"),
        ("organism_3", "Organism 3"),
    ]

    organisms: list[Organism] = []
    for internal_id, name in organism_details:
        organism: Organism = helpers.add_organism(store, internal_id=internal_id, name=name)
        organisms.append(organism)

    store.session.add_all(organisms)
    store.session.commit()
    yield store


@pytest.fixture(name="ok_response")
def ok_response() -> Response:
    """Return a response with the OK status code."""
    response: Response = Response()
    response.status_code = http.HTTPStatus.OK
    return response


@pytest.fixture(name="unauthorized_response")
def unauthorized_response() -> Response:
    """Return a response with the UNAUTHORIZED status code."""
    response: Response = Response()
    response.status_code = http.HTTPStatus.UNAUTHORIZED
    return response


@pytest.fixture(name="non_existent_email")
def non_existent_email():
    """Return email not associated with any entity."""
    return "non_existent_email@example.com"


@pytest.fixture(name="non_existent_id")
def non_existent_id():
    """Return id not associated with any entity."""
    return "non_existent_entity_id"


@pytest.fixture
def store_with_users(store: Store, helpers: StoreHelpers) -> Generator[Store, None, None]:
    """Return a store with multiple users."""

    customer: Customer = helpers.ensure_customer(store=store)

    user_details = [
        ("user1@example.com", "User One", False),
        ("user2@example.com", "User Two", True),
        ("user3@example.com", "User Three", False),
    ]

    for email, name, is_admin in user_details:
        user = store.add_user(customer=customer, email=email, name=name, is_admin=is_admin)
        store.session.add(user)

    store.session.commit()

    yield store


@pytest.fixture
def store_with_cases_and_customers(
    store: Store, helpers: StoreHelpers
) -> Generator[Store, None, None]:
    """Return a store with cases and customers."""

    customer_details: list[tuple[str, str, bool]] = [
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

    case_details: list[tuple[str, str, Workflow, CaseActions, Customer]] = [
        ("case 1", "flyingwhale", Workflow.BALSAMIC, CaseActions.RUNNING, customers[0]),
        ("case 2", "swimmingtiger", Workflow.FLUFFY, CaseActions.ANALYZE, customers[0]),
        ("case 3", "sadbaboon", Workflow.MUTANT, CaseActions.HOLD, customers[1]),
        ("case 4", "funkysloth", Workflow.MIP_DNA, CaseActions.ANALYZE, customers[1]),
        ("case 5", "deadparrot", Workflow.MICROSALT, CaseActions.RUNNING, customers[2]),
        ("case 6", "anxiousbeetle", Workflow.DEMULTIPLEX, CaseActions.RUNNING, customers[2]),
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


# Jasen fixtures


@pytest.fixture(scope="function")
def jasen_context(
    cg_context: CGConfig,
    helpers: StoreHelpers,
    nf_analysis_housekeeper: HousekeeperAPI,
    trailblazer_api: MockTB,
    hermes_api: HermesApi,
    cg_dir: Path,
) -> CGConfig:
    """Context to use in CLI."""
    cg_context.housekeeper_api_ = nf_analysis_housekeeper
    cg_context.trailblazer_api_ = trailblazer_api
    cg_context.meta_apis["analysis_api"] = JasenAnalysisAPI(config=cg_context)
    return cg_context


# NF analysis fixtures


@pytest.fixture(scope="session")
def no_sample_case_id() -> str:
    """Returns a case id of a case with no samples."""
    return "no_sample_case"


@pytest.fixture(scope="session")
def workflow_version() -> str:
    """Return a workflow version."""
    return "2.2.0"


@pytest.fixture(scope="session")
def fastq_forward_read_path(housekeeper_dir: Path) -> Path:
    """Path to existing fastq forward read file."""
    fastq_file_path = Path(housekeeper_dir, "XXXXXXXXX_000000_S000_L001_R1_001").with_suffix(
        f"{FileExtensions.FASTQ}{FileExtensions.GZIP}"
    )
    with gzip.open(fastq_file_path, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:1:1101:4806:1047 1:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_file_path


@pytest.fixture(scope="session")
def fastq_reverse_read_path(housekeeper_dir: Path) -> Path:
    """Path to existing fastq reverse read file."""
    fastq_file_path = Path(
        housekeeper_dir, "XXXXXXXXX_000000_S000_L001_R2_001.fastq.gz"
    ).with_suffix(f"{FileExtensions.FASTQ}{FileExtensions.GZIP}")
    with gzip.open(fastq_file_path, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:1:1101:4806:1047 2:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_file_path


@pytest.fixture(scope="session")
def mock_fastq_files(fastq_forward_read_path: Path, fastq_reverse_read_path: Path) -> list[Path]:
    """Return list of all mock fastq files to commit to mock housekeeper."""
    return [fastq_forward_read_path, fastq_reverse_read_path]


@pytest.fixture(scope="session")
def sequencing_platform() -> str:
    """Return a default sequencing platform."""
    return SequencingPlatform.ILLUMINA


# Raredisease fixtures
@pytest.fixture(scope="function")
def raredisease_dir(tmpdir_factory, apps_dir: Path) -> str:
    """Return the path to the raredisease apps dir."""
    raredisease_dir = tmpdir_factory.mktemp("raredisease")
    return Path(raredisease_dir).absolute().as_posix()


@pytest.fixture(scope="session")
def raredisease_case_id() -> str:
    """Returns a raredisease case id."""
    return "raredisease_case_enough_reads"


@pytest.fixture(scope="function")
def raredisease_sample_sheet_content(
    sample_id: str,
    raredisease_case_id: str,
    fastq_forward_read_path: Path,
    fastq_reverse_read_path: Path,
) -> str:
    """Return the expected sample sheet content  for raredisease."""
    headers: str = ",".join(RarediseaseSampleSheetHeaders.list())
    row: str = ",".join(
        [
            sample_id,
            "1",
            fastq_forward_read_path.as_posix(),
            fastq_reverse_read_path.as_posix(),
            "2",
            "0",
            "",
            "",
            raredisease_case_id,
        ]
    )
    return "\n".join([headers, row])


@pytest.fixture(scope="function")
def raredisease_sample_sheet_path(raredisease_dir, raredisease_case_id) -> Path:
    """Path to sample sheet."""
    return Path(
        raredisease_dir, raredisease_case_id, f"{raredisease_case_id}_samplesheet"
    ).with_suffix(FileExtensions.CSV)


@pytest.fixture(scope="function")
def raredisease_params_file_path(raredisease_dir, raredisease_case_id) -> Path:
    """Path to parameters file."""
    return Path(
        raredisease_dir, raredisease_case_id, f"{raredisease_case_id}_params_file"
    ).with_suffix(FileExtensions.YAML)


@pytest.fixture(scope="function")
def raredisease_gene_panel_path(raredisease_dir, raredisease_case_id) -> Path:
    """Path to gene panel file."""
    return Path(raredisease_dir, raredisease_case_id, "gene_panels").with_suffix(FileExtensions.BED)


@pytest.fixture(scope="function")
def raredisease_nexflow_config_file_path(raredisease_dir, raredisease_case_id) -> Path:
    """Path to config file."""
    return Path(
        raredisease_dir, raredisease_case_id, f"{raredisease_case_id}_nextflow_config"
    ).with_suffix(FileExtensions.JSON)


@pytest.fixture(scope="function")
def raredisease_deliverable_data(
    raredisease_dir: Path, raredisease_case_id: str, sample_id: str
) -> dict:
    return {
        "files": [
            {
                "path": f"{raredisease_dir}/{raredisease_case_id}/multiqc/multiqc_report.html",
                "path_index": "",
                "step": "report",
                "tag": ["multiqc-html"],
                "id": raredisease_case_id,
                "format": "html",
                "mandatory": True,
            },
        ]
    }


@pytest.fixture(scope="function")
def raredisease_deliverables_file_path(raredisease_dir, raredisease_case_id) -> Path:
    """Path to deliverables file."""
    return Path(
        raredisease_dir, raredisease_case_id, f"{raredisease_case_id}_deliverables"
    ).with_suffix(FileExtensions.YAML)


@pytest.fixture(scope="function")
def raredisease_parameters_default(
    raredisease_dir: Path,
    raredisease_case_id: str,
    raredisease_sample_sheet_path: Path,
    bed_version_file_name,
) -> RarediseaseParameters:
    """Return Tomte parameters."""
    return RarediseaseParameters(
        input=raredisease_sample_sheet_path,
        outdir=Path(raredisease_dir, raredisease_case_id),
        target_bed=bed_version_file_name,
        skip_germlinecnvcaller=False,
        analysis_type=AnalysisTypes.WES,
        save_mapped_as_cram=True,
        vcfanno_extra_resources=str(
            Path(raredisease_dir, raredisease_case_id + ScoutExportFileName.MANAGED_VARIANTS)
        ),
        local_genomes=Path(raredisease_dir, "references").as_posix(),
        vep_filters_scout_fmt=str(
            Path(raredisease_dir, raredisease_case_id + ScoutExportFileName.PANELS)
        ),
    )


@pytest.fixture(scope="function")
def raredisease_context(
    cg_context: CGConfig,
    helpers: StoreHelpers,
    nf_analysis_housekeeper: HousekeeperAPI,
    trailblazer_api: MockTB,
    raredisease_case_id: str,
    sample_id: str,
    father_sample_id: str,
    sample_name: str,
    another_sample_name: str,
    no_sample_case_id: str,
    total_sequenced_reads_pass: int,
    wgs_application_tag: str,
    case_id_not_enough_reads: str,
    sample_id_not_enough_reads: str,
    total_sequenced_reads_not_pass: int,
    mocker: MockFixture,
) -> CGConfig:
    """context to use in cli"""
    cg_context.housekeeper_api_ = nf_analysis_housekeeper
    cg_context.trailblazer_api_ = trailblazer_api
    cg_context.meta_apis["analysis_api"] = RarediseaseAnalysisAPI(config=cg_context)
    status_db: Store = cg_context.status_db

    # NB: the order in which the cases are added matters for the tests of store_available

    # Create ERROR case with NO SAMPLES
    helpers.add_case(status_db, internal_id=no_sample_case_id, name=no_sample_case_id)

    # Create textbook case with enough reads
    case_enough_reads: Case = helpers.add_case(
        store=status_db,
        internal_id=raredisease_case_id,
        name=raredisease_case_id,
        data_analysis=Workflow.RAREDISEASE,
    )

    sample_enough_reads: Sample = helpers.add_sample(
        status_db,
        internal_id=sample_id,
        name=sample_name,
        last_sequenced_at=datetime.now(),
        reads=total_sequenced_reads_pass,
        application_tag=wgs_application_tag,
        reference_genome=GenomeVersion.HG19,
    )

    another_sample_enough_reads: Sample = helpers.add_sample(
        status_db,
        internal_id=father_sample_id,
        name=another_sample_name,
        last_sequenced_at=datetime.now(),
        reads=total_sequenced_reads_pass,
        application_tag=wgs_application_tag,
        reference_genome=GenomeVersion.HG19,
    )

    helpers.add_relationship(
        status_db,
        case=case_enough_reads,
        sample=sample_enough_reads,
    )

    helpers.add_relationship(
        status_db,
        case=case_enough_reads,
        sample=another_sample_enough_reads,
    )

    # Create case without enough reads
    case_not_enough_reads: Case = helpers.add_case(
        store=status_db,
        internal_id=case_id_not_enough_reads,
        name=case_id_not_enough_reads,
        data_analysis=Workflow.RAREDISEASE,
    )

    sample_not_enough_reads: Sample = helpers.add_sample(
        status_db,
        internal_id=sample_id_not_enough_reads,
        last_sequenced_at=datetime.now(),
        reads=total_sequenced_reads_not_pass,
        application_tag=wgs_application_tag,
        reference_genome=GenomeVersion.HG19,
    )

    helpers.add_relationship(status_db, case=case_not_enough_reads, sample=sample_not_enough_reads)

    # GIVEN a genome build
    mocker.patch.object(RarediseaseAnalysisAPI, "get_genome_build", return_value=GenomeVersion.HG38)

    mocker.patch.object(RarediseaseAnalysisAPI, "get_target_bed_from_lims")
    RarediseaseAnalysisAPI.get_target_bed_from_lims.return_value = "some_target_bed_file"

    samples = [sample_enough_reads, another_sample_enough_reads]
    return cg_context


@pytest.fixture(scope="function")
def deliverable_data(raredisease_dir: Path, raredisease_case_id: str, sample_id: str) -> dict:
    return {
        "files": [
            {
                "path": f"{raredisease_dir}/{raredisease_case_id}/multiqc/multiqc_report.html",
                "path_index": "",
                "step": "report",
                "tag": ["multiqc-html", "rna"],
                "id": raredisease_case_id,
                "format": "html",
                "mandatory": True,
            },
        ]
    }


@pytest.fixture(scope="function")
def mock_deliverable(
    raredisease_dir: Path, deliverable_data: dict, raredisease_case_id: str
) -> None:
    """Create deliverable file with dummy data and files to deliver."""
    Path.mkdir(
        Path(raredisease_dir, raredisease_case_id),
        parents=True,
        exist_ok=True,
    )
    Path.mkdir(
        Path(raredisease_dir, raredisease_case_id, "multiqc"),
        parents=True,
        exist_ok=True,
    )
    for report_entry in deliverable_data["files"]:
        Path(report_entry["path"]).touch(exist_ok=True)
    WriteFile.write_file_from_content(
        content=deliverable_data,
        file_format=FileFormat.JSON,
        file_path=Path(
            raredisease_dir, raredisease_case_id, raredisease_case_id + deliverables_yaml
        ),
    )


@pytest.fixture(scope="function")
def raredisease_mock_config(raredisease_dir: Path, raredisease_case_id: str) -> None:
    """Create samplesheet.csv file for testing"""
    Path.mkdir(Path(raredisease_dir, raredisease_case_id), parents=True, exist_ok=True)
    Path(raredisease_dir, raredisease_case_id, f"{raredisease_case_id}_samplesheet").with_suffix(
        FileExtensions.CSV
    ).touch(exist_ok=True)


@pytest.fixture(scope="function")
def raredisease_metrics_deliverables(raredisease_analysis_dir: Path) -> list[dict]:
    """Returns the content of a mock metrics deliverables file."""
    return read_yaml(
        file_path=Path(
            raredisease_analysis_dir, "raredisease_case_enough_reads_metrics_deliverables.yaml"
        )
    )


@pytest.fixture(scope="function")
def raredisease_metrics_deliverables_path(raredisease_dir: Path, raredisease_case_id: str) -> Path:
    """Path to deliverables file."""
    return Path(
        raredisease_dir, raredisease_case_id, f"{raredisease_case_id}_metrics_deliverables"
    ).with_suffix(FileExtensions.YAML)


@pytest.fixture(scope="function")
def raredisease_mock_analysis_finish(
    raredisease_dir: Path,
    raredisease_case_id: str,
    raredisease_multiqc_json_metrics: dict,
    tower_id: int,
) -> None:
    """Create analysis finish file for testing."""
    Path.mkdir(
        Path(raredisease_dir, raredisease_case_id, "pipeline_info"), parents=True, exist_ok=True
    )
    Path(raredisease_dir, raredisease_case_id, "pipeline_info", software_version_file).touch(
        exist_ok=True
    )
    Path(raredisease_dir, raredisease_case_id, f"{raredisease_case_id}_samplesheet.csv").touch(
        exist_ok=True
    )
    Path.mkdir(
        Path(raredisease_dir, raredisease_case_id, "multiqc", "multiqc_data"),
        parents=True,
        exist_ok=True,
    )
    write_json(
        content=raredisease_multiqc_json_metrics,
        file_path=Path(
            raredisease_dir,
            raredisease_case_id,
            "multiqc",
            "multiqc_data",
            "multiqc_data",
        ).with_suffix(FileExtensions.JSON),
    )
    write_yaml(
        content={raredisease_case_id: [tower_id]},
        file_path=Path(
            raredisease_dir,
            raredisease_case_id,
            "tower_ids",
        ).with_suffix(FileExtensions.YAML),
    )


@pytest.fixture(scope="function")
def raredisease_mock_deliverable_dir(
    raredisease_dir: Path, raredisease_deliverable_data: dict, raredisease_case_id: str
) -> Path:
    """Create raredisease deliverable file with dummy data and files to deliver."""
    Path.mkdir(
        Path(raredisease_dir, raredisease_case_id),
        parents=True,
        exist_ok=True,
    )
    Path.mkdir(
        Path(raredisease_dir, raredisease_case_id, "multiqc"),
        parents=True,
        exist_ok=True,
    )
    for report_entry in raredisease_deliverable_data["files"]:
        Path(report_entry["path"]).touch(exist_ok=True)
    WriteFile.write_file_from_content(
        content=raredisease_deliverable_data,
        file_format=FileFormat.JSON,
        file_path=Path(
            raredisease_dir, raredisease_case_id, raredisease_case_id + deliverables_yaml
        ),
    )
    return raredisease_dir


@pytest.fixture(scope="function")
def raredisease_hermes_deliverables(
    raredisease_deliverable_data: dict, raredisease_case_id: str
) -> dict:
    hermes_output: dict = {"workflow": "raredisease", "bundle_id": raredisease_case_id, "files": []}
    for file_info in raredisease_deliverable_data["files"]:
        tags: list[str] = []
        if "html" in file_info["format"]:
            tags.append("multiqc-html")
        hermes_output["files"].append({"path": file_info["path"], "tags": tags, "mandatory": True})
    return hermes_output


@pytest.fixture(scope="function")
def raredisease_malformed_hermes_deliverables(raredisease_hermes_deliverables: dict) -> dict:
    malformed_deliverable: dict = raredisease_hermes_deliverables.copy()
    malformed_deliverable.pop("workflow")
    return malformed_deliverable


@pytest.fixture(scope="function")
def raredisease_deliverables_response_data(
    create_multiqc_html_file,
    create_multiqc_json_file,
    raredisease_case_id,
    timestamp_yesterday,
) -> InputBundle:
    return InputBundle(
        **{
            "files": [
                {
                    "path": create_multiqc_json_file.as_posix(),
                    "tags": ["multiqc-json", raredisease_case_id],
                },
                {
                    "path": create_multiqc_html_file.as_posix(),
                    "tags": ["multiqc-html", raredisease_case_id],
                },
            ],
            "created": timestamp_yesterday,
            "name": raredisease_case_id,
        }
    )


@pytest.fixture
def raredisease_multiqc_json_metrics_path(raredisease_analysis_dir: Path) -> Path:
    """Return Multiqc JSON file path for Raredisease."""
    return Path(raredisease_analysis_dir, multiqc_json_file)


@pytest.fixture
def raredisease_multiqc_json_metrics(raredisease_multiqc_json_metrics_path: Path) -> list[dict]:
    """Returns the content of a mock Multiqc JSON file."""
    return read_json(file_path=raredisease_multiqc_json_metrics_path)


# Rnafusion fixtures


@pytest.fixture(scope="function")
def rnafusion_dir(tmpdir_factory, apps_dir: Path) -> str:
    """Return the path to the rnafusion apps dir."""
    rnafusion_dir = tmpdir_factory.mktemp("rnafusion")
    return Path(rnafusion_dir).absolute().as_posix()


@pytest.fixture(scope="session")
def rnafusion_case_id() -> str:
    """Returns a rnafusion case id."""
    return "rnafusion_case_enough_reads"


@pytest.fixture(scope="session")
def rnafusion_workflow() -> str:
    """Returns rnafusion workflow."""
    return "rnafusion"


@pytest.fixture(scope="function")
def rnafusion_sample_sheet_content(
    rnafusion_case_id: str,
    sample_id: str,
    fastq_forward_read_path: Path,
    fastq_reverse_read_path: Path,
    strandedness: str,
) -> str:
    """Return the expected sample sheet content  for rnafusion."""
    headers: str = ",".join(RnafusionSampleSheetEntry.headers())
    row: str = ",".join(
        [
            sample_id,
            fastq_forward_read_path.as_posix(),
            fastq_reverse_read_path.as_posix(),
            strandedness,
        ]
    )
    return "\n".join([headers, row])


@pytest.fixture(scope="session")
def strandedness_not_permitted() -> str:
    """Return a not permitted strandedness."""
    return "double_stranded"


@pytest.fixture(scope="function")
def rnafusion_hermes_deliverables(rnafusion_deliverable_data: dict, rnafusion_case_id: str) -> dict:
    hermes_output: dict = {"workflow": "rnafusion", "bundle_id": rnafusion_case_id, "files": []}
    for file_info in rnafusion_deliverable_data["files"]:
        tags: list[str] = []
        if "html" in file_info["format"]:
            tags.append("multiqc-html")
        hermes_output["files"].append({"path": file_info["path"], "tags": tags, "mandatory": True})
    return hermes_output


@pytest.fixture(scope="function")
def rnafusion_malformed_hermes_deliverables(rnafusion_hermes_deliverables: dict) -> dict:
    malformed_deliverable: dict = rnafusion_hermes_deliverables.copy()
    malformed_deliverable.pop("workflow")

    return malformed_deliverable


@pytest.fixture
def rnafusion_multiqc_json_metrics_path(rnafusion_analysis_dir: Path) -> Path:
    """Return Multiqc JSON file path for Raredisease."""
    return Path(rnafusion_analysis_dir, multiqc_json_file)


@pytest.fixture
def rnafusion_multiqc_json_metrics(rnafusion_multiqc_json_metrics_path: Path) -> list[dict]:
    """Returns the content of a mock Multiqc JSON file."""
    return read_json(file_path=rnafusion_multiqc_json_metrics_path)


@pytest.fixture(scope="function")
def rnafusion_sample_sheet_path(rnafusion_dir, rnafusion_case_id) -> Path:
    """Path to sample sheet."""
    return Path(rnafusion_dir, rnafusion_case_id, f"{rnafusion_case_id}_samplesheet").with_suffix(
        FileExtensions.CSV
    )


@pytest.fixture(scope="function")
def rnafusion_params_file_path(rnafusion_dir, rnafusion_case_id) -> Path:
    """Path to parameters file."""
    return Path(rnafusion_dir, rnafusion_case_id, f"{rnafusion_case_id}_params_file").with_suffix(
        FileExtensions.YAML
    )


@pytest.fixture(scope="function")
def rnafusion_nexflow_config_file_path(rnafusion_dir, rnafusion_case_id) -> Path:
    """Path to config file."""
    return Path(
        rnafusion_dir, rnafusion_case_id, f"{rnafusion_case_id}_nextflow_config"
    ).with_suffix(FileExtensions.JSON)


@pytest.fixture(scope="function")
def rnafusion_metrics_deliverables(rnafusion_analysis_dir: Path) -> list[dict]:
    """Returns the content of a mock metrics deliverables file."""
    return read_yaml(
        file_path=Path(
            rnafusion_analysis_dir, "rnafusion_case_enough_reads_metrics_deliverables.yaml"
        )
    )


@pytest.fixture(scope="function")
def rnafusion_metrics_deliverables_path(rnafusion_dir: Path, rnafusion_case_id: str) -> Path:
    """Path to deliverables file."""
    return Path(
        rnafusion_dir, rnafusion_case_id, f"{rnafusion_case_id}_metrics_deliverables"
    ).with_suffix(FileExtensions.YAML)


@pytest.fixture(scope="function")
def rnafusion_deliverables_file_path(rnafusion_dir, rnafusion_case_id) -> Path:
    """Path to deliverables file."""
    return Path(rnafusion_dir, rnafusion_case_id, f"{rnafusion_case_id}_deliverables").with_suffix(
        FileExtensions.YAML
    )


@pytest.fixture(scope="function")
def nf_analysis_platform_config_path(nf_analysis_analysis_dir) -> Path:
    """Path to platform config file."""
    return Path(nf_analysis_analysis_dir, "platform").with_suffix(FileExtensions.CONFIG)


@pytest.fixture(scope="function")
def nf_analysis_pipeline_params_path(nf_analysis_analysis_dir) -> Path:
    """Path to pipeline params file."""
    return Path(nf_analysis_analysis_dir, "pipeline_params").with_suffix(FileExtensions.CONFIG)


@pytest.fixture(scope="function")
def rnafusion_deliverables_response_data(
    create_multiqc_html_file,
    create_multiqc_json_file,
    rnafusion_case_id,
    timestamp_yesterday,
) -> InputBundle:
    return InputBundle(
        **{
            "files": [
                {
                    "path": create_multiqc_json_file.as_posix(),
                    "tags": ["multiqc-json", rnafusion_case_id],
                },
                {
                    "path": create_multiqc_html_file.as_posix(),
                    "tags": ["multiqc-html", rnafusion_case_id],
                },
            ],
            "created": timestamp_yesterday,
            "name": rnafusion_case_id,
        }
    )


@pytest.fixture(scope="function")
def nf_analysis_pipeline_resource_optimisation_path(nf_analysis_analysis_dir) -> Path:
    """Path to pipeline resource optimisation file."""
    return Path(nf_analysis_analysis_dir, "pipeline_resource_optimisation").with_suffix(
        FileExtensions.CONFIG
    )


@pytest.fixture(scope="session")
def tower_id() -> int:
    """Returns a NF-Tower ID."""
    return 123456


@pytest.fixture(scope="session")
def existing_directory(tmpdir_factory) -> Path:
    """Path to existing temporary directory."""
    return tmpdir_factory.mktemp("any_directory")


@pytest.fixture(scope="function")
def rnafusion_parameters_default(
    rnafusion_dir: Path,
    rnafusion_case_id: str,
    rnafusion_sample_sheet_path: Path,
    existing_directory: Path,
) -> RnafusionParameters:
    """Return Rnafusion parameters."""
    return RnafusionParameters(
        cluster_options="--qos=normal",
        genomes_base=Path(existing_directory),
        input=rnafusion_sample_sheet_path,
        outdir=Path(rnafusion_dir, rnafusion_case_id),
        priority="development",
    )


@pytest.fixture(scope="session")
def total_sequenced_reads_pass() -> int:
    return 200_000_000


@pytest.fixture(scope="session")
def total_sequenced_reads_not_pass() -> int:
    return 0


@pytest.fixture(scope="function")
def rnafusion_context(
    cg_context: CGConfig,
    helpers: StoreHelpers,
    nf_analysis_housekeeper: HousekeeperAPI,
    trailblazer_api: MockTB,
    hermes_api: HermesApi,
    cg_dir: Path,
    rnafusion_case_id: str,
    sample_id: str,
    no_sample_case_id: str,
    total_sequenced_reads_pass: int,
    apptag_rna: str,
    case_id_not_enough_reads: str,
    sample_id_not_enough_reads: str,
    total_sequenced_reads_not_pass: int,
) -> CGConfig:
    """context to use in cli"""
    cg_context.housekeeper_api_ = nf_analysis_housekeeper
    cg_context.trailblazer_api_ = trailblazer_api
    cg_context.meta_apis["analysis_api"] = RnafusionAnalysisAPI(config=cg_context)
    status_db: Store = cg_context.status_db

    # NB: the order in which the cases are added matters for the tests of store_available

    # Create case with no associated samples
    helpers.add_case(status_db, internal_id=no_sample_case_id, name=no_sample_case_id)

    # Create textbook case with enough reads
    case_enough_reads: Case = helpers.add_case(
        store=status_db,
        internal_id=rnafusion_case_id,
        name=rnafusion_case_id,
        data_analysis=Workflow.RNAFUSION,
    )

    sample_rnafusion_case_enough_reads: Sample = helpers.add_sample(
        status_db,
        application_tag=apptag_rna,
        internal_id=sample_id,
        reads=total_sequenced_reads_pass,
        last_sequenced_at=datetime.now(),
    )

    helpers.add_relationship(
        status_db,
        case=case_enough_reads,
        sample=sample_rnafusion_case_enough_reads,
    )
    # Create case without enough reads
    case_not_enough_reads: Case = helpers.add_case(
        store=status_db,
        internal_id=case_id_not_enough_reads,
        name=case_id_not_enough_reads,
        data_analysis=Workflow.RNAFUSION,
    )

    sample_not_enough_reads: Sample = helpers.add_sample(
        status_db,
        application_tag=apptag_rna,
        internal_id=sample_id_not_enough_reads,
        reads=total_sequenced_reads_not_pass,
        last_sequenced_at=datetime.now(),
    )

    helpers.add_relationship(status_db, case=case_not_enough_reads, sample=sample_not_enough_reads)

    return cg_context


@pytest.fixture(scope="function")
def rnafusion_deliverable_data(rnafusion_dir: Path, rnafusion_case_id: str, sample_id: str) -> dict:
    return {
        "files": [
            {
                "path": f"{rnafusion_dir}/{rnafusion_case_id}/multiqc/multiqc_report.html",
                "path_index": "",
                "step": "report",
                "tag": ["multiqc-html", "rna"],
                "id": sample_id,
                "format": "html",
                "mandatory": True,
            },
        ]
    }


@pytest.fixture(scope="function")
def rnafusion_mock_deliverable_dir(
    rnafusion_dir: Path, rnafusion_deliverable_data: dict, rnafusion_case_id: str
) -> Path:
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
    for report_entry in rnafusion_deliverable_data["files"]:
        Path(report_entry["path"]).touch(exist_ok=True)
    WriteFile.write_file_from_content(
        content=rnafusion_deliverable_data,
        file_format=FileFormat.JSON,
        file_path=Path(rnafusion_dir, rnafusion_case_id, rnafusion_case_id + deliverables_yaml),
    )
    return rnafusion_dir


@pytest.fixture(scope="function")
def rnafusion_mock_analysis_finish(
    rnafusion_dir: Path, rnafusion_case_id: str, rnafusion_multiqc_json_metrics: dict, tower_id: int
) -> None:
    """Create analysis_finish file for testing."""
    Path.mkdir(Path(rnafusion_dir, rnafusion_case_id, "pipeline_info"), parents=True, exist_ok=True)
    Path(rnafusion_dir, rnafusion_case_id, "pipeline_info", software_version_file).touch(
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


@pytest.fixture(scope="function")
def rnafusion_mock_config(rnafusion_dir: Path, rnafusion_case_id: str) -> None:
    """Create samplesheet.csv file for testing"""
    Path.mkdir(Path(rnafusion_dir, rnafusion_case_id), parents=True, exist_ok=True)
    Path(rnafusion_dir, rnafusion_case_id, f"{rnafusion_case_id}_samplesheet.csv").with_suffix(
        FileExtensions.CSV
    ).touch(exist_ok=True)


# Tomte fixtures
@pytest.fixture(scope="session")
def tomte_case_id() -> str:
    """Returns a tomte case id."""
    return "tomte_case_enough_reads"


@pytest.fixture(scope="function")
def tomte_dir(tmpdir_factory, apps_dir: Path) -> str:
    """Return the path to the tomte apps dir."""
    tomte_dir = tmpdir_factory.mktemp("tomte")
    return Path(tomte_dir).absolute().as_posix()


@pytest.fixture(scope="function")
def tomte_sample_sheet_path(tomte_dir, tomte_case_id) -> Path:
    """Path to sample sheet."""
    return Path(tomte_dir, tomte_case_id, f"{tomte_case_id}_samplesheet").with_suffix(
        FileExtensions.CSV
    )


@pytest.fixture(scope="function")
def tomte_params_file_path(tomte_dir, tomte_case_id) -> Path:
    """Path to parameters file."""
    return Path(tomte_dir, tomte_case_id, f"{tomte_case_id}_params_file").with_suffix(
        FileExtensions.YAML
    )


@pytest.fixture(scope="function")
def tomte_nexflow_config_file_path(tomte_dir, tomte_case_id) -> Path:
    """Path to config file."""
    return Path(tomte_dir, tomte_case_id, f"{tomte_case_id}_nextflow_config").with_suffix(
        FileExtensions.JSON
    )


@pytest.fixture(scope="function")
def tomte_gene_panel_path(tomte_dir, tomte_case_id) -> Path:
    """Path to gene panel file."""
    return Path(tomte_dir, tomte_case_id, "gene_panels").with_suffix(FileExtensions.BED)


@pytest.fixture(scope="function")
def tomte_mock_config(tomte_dir: Path, tomte_case_id: str) -> None:
    """Create Tomte samplesheet.csv file for testing."""
    Path.mkdir(Path(tomte_dir, tomte_case_id), parents=True, exist_ok=True)
    Path(tomte_dir, tomte_case_id, f"{tomte_case_id}_samplesheet").with_suffix(
        FileExtensions.CSV
    ).touch(exist_ok=True)


@pytest.fixture(scope="function")
def tomte_metrics_deliverables_path(tomte_dir: Path, tomte_case_id: str) -> Path:
    """Path to deliverables file."""
    return Path(tomte_dir, tomte_case_id, f"{tomte_case_id}_metrics_deliverables").with_suffix(
        FileExtensions.YAML
    )


@pytest.fixture(scope="function")
def tomte_metrics_deliverables(tomte_analysis_dir: Path) -> list[dict]:
    """Returns the content of a mock metrics deliverables file."""
    return read_yaml(
        file_path=Path(tomte_analysis_dir, "tomte_case_enough_reads_metrics_deliverables.yaml")
    )


@pytest.fixture(scope="function")
def tomte_deliverable_data(tomte_dir: Path, tomte_case_id: str, sample_id: str) -> dict:
    return {
        "files": [
            {
                "path": f"{tomte_dir}/{tomte_case_id}/multiqc/multiqc_report.html",
                "path_index": "",
                "step": "report",
                "tag": ["multiqc-html", "rna"],
                "id": tomte_case_id,
                "format": "html",
                "mandatory": True,
            },
        ]
    }


@pytest.fixture(scope="function")
def tomte_multiqc_json_metrics(tomte_analysis_dir) -> dict:
    """Returns the content of a mock Multiqc JSON file."""
    return read_json(file_path=Path(tomte_analysis_dir, multiqc_json_file))


@pytest.fixture
def tomte_analysis_dir(analysis_dir: Path) -> Path:
    """Return the path to the directory with Tomte analysis files."""
    return Path(analysis_dir, "tomte")


@pytest.fixture(scope="function")
def tomte_mock_deliverable_dir(
    tomte_dir: Path, tomte_deliverable_data: dict, tomte_case_id: str
) -> Path:
    """Create deliverable file with dummy data and files to deliver."""
    Path.mkdir(
        Path(tomte_dir, tomte_case_id),
        parents=True,
        exist_ok=True,
    )
    Path.mkdir(
        Path(tomte_dir, tomte_case_id, "multiqc"),
        parents=True,
        exist_ok=True,
    )
    for report_entry in tomte_deliverable_data["files"]:
        Path(report_entry["path"]).touch(exist_ok=True)
    WriteFile.write_file_from_content(
        content=tomte_deliverable_data,
        file_format=FileFormat.JSON,
        file_path=Path(tomte_dir, tomte_case_id, tomte_case_id + deliverables_yaml),
    )

    return tomte_dir


@pytest.fixture(scope="session")
def strandedness() -> str:
    """Return a default strandedness."""
    return Strandedness.REVERSE


@pytest.fixture(scope="function")
def tomte_sample_sheet_content(
    tomte_case_id: str,
    sample_id: str,
    fastq_forward_read_path: Path,
    fastq_reverse_read_path: Path,
    strandedness: str,
) -> str:
    """Return the expected sample sheet content for tomte."""
    headers: str = ",".join(TomteSampleSheetHeaders.list())
    row: str = ",".join(
        [
            tomte_case_id,
            sample_id,
            fastq_forward_read_path.as_posix(),
            fastq_reverse_read_path.as_posix(),
            strandedness,
        ]
    )
    return "\n".join([headers, row])


@pytest.fixture(scope="function")
def tomte_mock_analysis_finish(
    tomte_dir: Path, tomte_case_id: str, tomte_multiqc_json_metrics: dict, tower_id: int
) -> None:
    """Create analysis_finish file for testing."""
    Path.mkdir(Path(tomte_dir, tomte_case_id, "pipeline_info"), parents=True, exist_ok=True)
    Path(tomte_dir, tomte_case_id, "pipeline_info", software_version_file).touch(exist_ok=True)
    Path(tomte_dir, tomte_case_id, f"{tomte_case_id}_samplesheet.csv").touch(exist_ok=True)
    Path.mkdir(
        Path(tomte_dir, tomte_case_id, "multiqc", "multiqc_data"),
        parents=True,
        exist_ok=True,
    )
    write_json(
        content=tomte_multiqc_json_metrics,
        file_path=Path(
            tomte_dir,
            tomte_case_id,
            "multiqc",
            "multiqc_data",
            "multiqc_data",
        ).with_suffix(FileExtensions.JSON),
    )
    write_yaml(
        content={tomte_case_id: [tower_id]},
        file_path=Path(
            tomte_dir,
            tomte_case_id,
            "tower_ids",
        ).with_suffix(FileExtensions.YAML),
    )


@pytest.fixture(scope="function")
def tomte_deliverables_file_path(tomte_dir, tomte_case_id) -> Path:
    """Path to deliverables file."""
    return Path(tomte_dir, tomte_case_id, f"{tomte_case_id}_deliverables").with_suffix(
        FileExtensions.YAML
    )


@pytest.fixture(scope="function")
def tomte_hermes_deliverables(tomte_deliverable_data: dict, tomte_case_id: str) -> dict:
    hermes_output: dict = {"workflow": "tomte", "bundle_id": tomte_case_id, "files": []}
    for file_info in tomte_deliverable_data["files"]:
        tags: list[str] = []
        if "html" in file_info["format"]:
            tags.append("multiqc-html")
        hermes_output["files"].append({"path": file_info["path"], "tags": tags, "mandatory": True})
    return hermes_output


@pytest.fixture(scope="function")
def tomte_malformed_hermes_deliverables(tomte_hermes_deliverables: dict) -> dict:
    malformed_deliverable: dict = tomte_hermes_deliverables.copy()
    malformed_deliverable.pop("workflow")
    return malformed_deliverable


@pytest.fixture(scope="function")
def tomte_deliverables_response_data(
    create_multiqc_html_file,
    create_multiqc_json_file,
    tomte_case_id,
    timestamp_yesterday,
) -> InputBundle:
    return InputBundle(
        **{
            "files": [
                {
                    "path": create_multiqc_json_file.as_posix(),
                    "tags": ["multiqc-json", tomte_case_id],
                },
                {
                    "path": create_multiqc_html_file.as_posix(),
                    "tags": ["multiqc-html", tomte_case_id],
                },
            ],
            "created": timestamp_yesterday,
            "name": tomte_case_id,
        }
    )


@pytest.fixture(scope="function")
def tomte_parameters_default(
    tomte_dir: Path,
    tomte_case_id: str,
    tomte_sample_sheet_path: Path,
    tomte_gene_panel_path: Path,
    existing_directory: Path,
) -> TomteParameters:
    """Return Tomte parameters."""
    return TomteParameters(
        input=tomte_sample_sheet_path,
        outdir=Path(tomte_dir, tomte_case_id),
        gene_panel_clinical_filter=tomte_gene_panel_path,
        tissue="unkown",
        genome="hg38",
    )


@pytest.fixture(scope="function")
def tomte_context(
    cg_context: CGConfig,
    helpers: StoreHelpers,
    nf_analysis_housekeeper: HousekeeperAPI,
    trailblazer_api: MockTB,
    hermes_api: HermesApi,
    cg_dir: Path,
    tomte_case_id: str,
    sample_id: str,
    no_sample_case_id: str,
    total_sequenced_reads_pass: int,
    apptag_rna: str,
    case_id_not_enough_reads: str,
    sample_id_not_enough_reads: str,
    total_sequenced_reads_not_pass: int,
) -> CGConfig:
    """Context to use in CLI."""
    cg_context.housekeeper_api_ = nf_analysis_housekeeper
    cg_context.trailblazer_api_ = trailblazer_api
    cg_context.meta_apis["analysis_api"] = TomteAnalysisAPI(config=cg_context)
    status_db: Store = cg_context.status_db

    # NB: the order in which the cases are added matters for the tests of store_available

    # Create ERROR case with NO SAMPLES
    helpers.add_case(status_db, internal_id=no_sample_case_id, name=no_sample_case_id)

    # Create a textbook case with enough reads
    case_enough_reads: Case = helpers.add_case(
        store=status_db,
        internal_id=tomte_case_id,
        name=tomte_case_id,
        data_analysis=Workflow.TOMTE,
        panels=[GenePanelMasterList.OMIM_AUTO],
    )

    sample_enough_reads: Sample = helpers.add_sample(
        status_db,
        application_tag=apptag_rna,
        internal_id=sample_id,
        reads=total_sequenced_reads_pass,
        last_sequenced_at=datetime.now(),
        reference_genome=GenomeVersion.HG38,
    )

    helpers.add_relationship(
        status_db,
        case=case_enough_reads,
        sample=sample_enough_reads,
    )

    # Create a case without enough reads
    case_not_enough_reads: Case = helpers.add_case(
        store=status_db,
        internal_id=case_id_not_enough_reads,
        name=case_id_not_enough_reads,
        data_analysis=Workflow.TOMTE,
    )

    sample_not_enough_reads: Sample = helpers.add_sample(
        status_db,
        application_tag=apptag_rna,
        internal_id=sample_id_not_enough_reads,
        reads=total_sequenced_reads_not_pass,
        last_sequenced_at=datetime.now(),
    )

    helpers.add_relationship(status_db, case=case_not_enough_reads, sample=sample_not_enough_reads)

    return cg_context


# Taxprofiler fixtures


@pytest.fixture(scope="function")
def taxprofiler_config(taxprofiler_dir: Path, taxprofiler_case_id: str) -> None:
    """Create CSV sample sheet file for testing."""
    Path.mkdir(Path(taxprofiler_dir, taxprofiler_case_id), parents=True, exist_ok=True)
    Path(taxprofiler_dir, taxprofiler_case_id, f"{taxprofiler_case_id}_samplesheet").with_suffix(
        FileExtensions.CSV
    ).touch(exist_ok=True)


@pytest.fixture(scope="session")
def taxprofiler_case_id() -> str:
    """Returns a taxprofiler case id."""
    return "taxprofiler_case"


@pytest.fixture(scope="session")
def taxprofiler_workflow() -> str:
    """Returns taxprofiler workflow."""
    return "taxprofiler"


@pytest.fixture(scope="function")
def taxprofiler_dir(tmpdir_factory, apps_dir: Path) -> Path:
    """Return the path to the Taxprofiler directory."""
    taxprofiler_dir = tmpdir_factory.mktemp("taxprofiler")
    return Path(taxprofiler_dir).absolute().as_posix()


@pytest.fixture(scope="function")
def taxprofiler_sample_sheet_path(taxprofiler_dir, taxprofiler_case_id) -> Path:
    """Path to sample sheet."""
    return Path(
        taxprofiler_dir, taxprofiler_case_id, f"{taxprofiler_case_id}_samplesheet"
    ).with_suffix(FileExtensions.CSV)


@pytest.fixture(scope="function")
def taxprofiler_nexflow_config_file_path(taxprofiler_dir, taxprofiler_case_id) -> Path:
    """Path to config file."""
    return Path(
        taxprofiler_dir, taxprofiler_case_id, f"{taxprofiler_case_id}_nextflow_config"
    ).with_suffix(FileExtensions.JSON)


@pytest.fixture(scope="function")
def taxprofiler_sample_sheet_content(
    sample_name: str,
    sequencing_platform: str,
    fastq_forward_read_path: Path,
    fastq_reverse_read_path: Path,
) -> str:
    """Return the expected sample sheet content  for taxprofiler."""
    headers: str = ",".join(TaxprofilerSampleSheetEntry.headers())
    row: str = ",".join(
        [
            sample_name,
            "1",
            sequencing_platform,
            fastq_forward_read_path.as_posix(),
            fastq_reverse_read_path.as_posix(),
            "",
        ]
    )
    return "\n".join([headers, row])


@pytest.fixture(scope="function")
def taxprofiler_params_file_path(taxprofiler_dir, taxprofiler_case_id) -> Path:
    """Path to parameters file."""
    return Path(
        taxprofiler_dir, taxprofiler_case_id, f"{taxprofiler_case_id}_params_file"
    ).with_suffix(FileExtensions.YAML)


@pytest.fixture(scope="function")
def taxprofiler_hermes_deliverables(
    taxprofiler_deliverable_data: dict, taxprofiler_case_id: str
) -> dict:
    hermes_output: dict = {"workflow": "taxprofiler", "bundle_id": taxprofiler_case_id, "files": []}
    for file_info in taxprofiler_deliverable_data["files"]:
        tags: list[str] = []
        if "html" in file_info["format"]:
            tags.append("multiqc-html")
        hermes_output["files"].append({"path": file_info["path"], "tags": tags, "mandatory": True})
    return hermes_output


@pytest.fixture(scope="function")
def taxprofiler_malformed_hermes_deliverables(taxprofiler_hermes_deliverables: dict) -> dict:
    malformed_deliverable: dict = taxprofiler_hermes_deliverables.copy()
    malformed_deliverable.pop("workflow")
    return malformed_deliverable


@pytest.fixture(scope="function")
def taxprofiler_parameters_default(
    taxprofiler_dir: Path,
    taxprofiler_case_id: str,
    taxprofiler_sample_sheet_path: Path,
    existing_directory: Path,
) -> TaxprofilerParameters:
    """Return Taxprofiler parameters."""
    return TaxprofilerParameters(
        cluster_options="--qos=normal",
        input=taxprofiler_sample_sheet_path,
        outdir=Path(taxprofiler_dir, taxprofiler_case_id),
        databases=Path(existing_directory),
        hostremoval_reference=Path(existing_directory),
        priority="development",
    )


@pytest.fixture(scope="function")
def taxprofiler_multiqc_json_metrics(taxprofiler_analysis_dir: Path) -> list[dict]:
    """Returns the content of a mock Multiqc JSON file."""
    return read_json(file_path=Path(taxprofiler_analysis_dir, multiqc_json_file))


@pytest.fixture(scope="function")
def taxprofiler_metrics_deliverables(taxprofiler_analysis_dir: Path) -> dict:
    """Returns the content of a mock metrics deliverables file."""
    return read_yaml(
        file_path=Path(taxprofiler_analysis_dir, "taxprofiler_case_metrics_deliverables.yaml")
    )


@pytest.fixture(scope="function")
def taxprofiler_metrics_deliverables_path(taxprofiler_dir: Path, taxprofiler_case_id: str) -> Path:
    """Path to deliverables file."""
    return Path(
        taxprofiler_dir, taxprofiler_case_id, f"{taxprofiler_case_id}_metrics_deliverables"
    ).with_suffix(FileExtensions.YAML)


@pytest.fixture(scope="function")
def taxprofiler_deliverables_file_path(taxprofiler_dir: Path, taxprofiler_case_id: str) -> Path:
    """Path to deliverables file."""
    return Path(
        taxprofiler_dir, taxprofiler_case_id, f"{taxprofiler_case_id}_deliverables"
    ).with_suffix(FileExtensions.YAML)


@pytest.fixture(scope="function")
def taxprofiler_context(
    cg_context: CGConfig,
    helpers: StoreHelpers,
    trailblazer_api: MockTB,
    hermes_api: HermesApi,
    nf_analysis_housekeeper: HousekeeperAPI,
    cg_dir: Path,
    taxprofiler_case_id: str,
    sample_id: str,
    father_sample_id: str,
    sample_name: str,
    another_sample_name: str,
    no_sample_case_id: str,
    total_sequenced_reads_pass: int,
    metagenomics_application_tag: str,
    case_id_not_enough_reads: str,
    sample_id_not_enough_reads: str,
    total_sequenced_reads_not_pass: int,
) -> CGConfig:
    """Context to use in cli."""
    cg_context.housekeeper_api_ = nf_analysis_housekeeper
    cg_context.trailblazer_api_ = trailblazer_api
    cg_context.meta_apis["analysis_api"] = TaxprofilerAnalysisAPI(config=cg_context)
    status_db: Store = cg_context.status_db

    # NB: the order in which the cases are added matters for the tests of store_available

    # Create case with no associate samples
    helpers.add_case(status_db, internal_id=no_sample_case_id, name=no_sample_case_id)

    # Create case with associated samples
    taxprofiler_case: Case = helpers.add_case(
        store=status_db,
        internal_id=taxprofiler_case_id,
        name=taxprofiler_case_id,
        data_analysis=Workflow.TAXPROFILER,
    )

    taxprofiler_sample: Sample = helpers.add_sample(
        status_db,
        application_tag="multiqc",
        internal_id=sample_id,
        reads=total_sequenced_reads_pass,
        name=sample_name,
        last_sequenced_at=datetime.now(),
    )

    taxprofiler_another_sample: Sample = helpers.add_sample(
        status_db,
        application_tag="multiqc",
        internal_id=father_sample_id,
        last_sequenced_at=datetime.now(),
        name=another_sample_name,
        reads=total_sequenced_reads_pass,
    )

    helpers.add_relationship(
        status_db,
        case=taxprofiler_case,
        sample=taxprofiler_sample,
    )

    helpers.add_relationship(
        status_db,
        case=taxprofiler_case,
        sample=taxprofiler_another_sample,
    )

    # Create case without enough reads
    case_not_enough_reads: Case = helpers.add_case(
        store=status_db,
        internal_id=case_id_not_enough_reads,
        name=case_id_not_enough_reads,
        data_analysis=Workflow.TAXPROFILER,
    )

    sample_not_enough_reads: Sample = helpers.add_sample(
        status_db,
        application_tag=metagenomics_application_tag,
        internal_id=sample_id_not_enough_reads,
        reads=total_sequenced_reads_not_pass,
        last_sequenced_at=datetime.now(),
    )

    helpers.add_relationship(status_db, case=case_not_enough_reads, sample=sample_not_enough_reads)

    return cg_context


@pytest.fixture(scope="function")
def taxprofiler_deliverable_data(
    taxprofiler_dir: Path, taxprofiler_case_id: str, sample_id: str
) -> dict:
    return {
        "files": [
            {
                "path": f"{taxprofiler_dir}/{taxprofiler_case_id}/multiqc/multiqc_report.html",
                "path_index": "",
                "step": "report",
                "tag": ["multiqc-html", "rna"],
                "id": taxprofiler_case_id,
                "format": "html",
                "mandatory": True,
            },
        ]
    }


@pytest.fixture(scope="function")
def taxprofiler_mock_deliverable_dir(
    taxprofiler_dir: Path, taxprofiler_deliverable_data: dict, taxprofiler_case_id: str
) -> Path:
    """Create taxprofiler deliverable file with dummy data and files to deliver."""
    Path.mkdir(
        Path(taxprofiler_dir, taxprofiler_case_id),
        parents=True,
        exist_ok=True,
    )
    Path.mkdir(
        Path(taxprofiler_dir, taxprofiler_case_id, "multiqc"),
        parents=True,
        exist_ok=True,
    )
    for report_entry in taxprofiler_deliverable_data["files"]:
        Path(report_entry["path"]).touch(exist_ok=True)
    WriteFile.write_file_from_content(
        content=taxprofiler_deliverable_data,
        file_format=FileFormat.JSON,
        file_path=Path(
            taxprofiler_dir, taxprofiler_case_id, taxprofiler_case_id + deliverables_yaml
        ),
    )
    return taxprofiler_dir


@pytest.fixture(scope="function")
def taxprofiler_mock_analysis_finish(
    taxprofiler_dir: Path,
    taxprofiler_case_id: str,
    taxprofiler_multiqc_json_metrics: dict,
    tower_id: int,
) -> None:
    """Create analysis_finish file for testing."""
    Path.mkdir(
        Path(taxprofiler_dir, taxprofiler_case_id, "pipeline_info"), parents=True, exist_ok=True
    )
    Path(taxprofiler_dir, taxprofiler_case_id, "pipeline_info", software_version_file).touch(
        exist_ok=True
    )
    Path(taxprofiler_dir, taxprofiler_case_id, f"{taxprofiler_case_id}_samplesheet.csv").touch(
        exist_ok=True
    )
    Path.mkdir(
        Path(taxprofiler_dir, taxprofiler_case_id, "multiqc", "multiqc_data"),
        parents=True,
        exist_ok=True,
    )
    write_json(
        content=taxprofiler_multiqc_json_metrics,
        file_path=Path(
            taxprofiler_dir,
            taxprofiler_case_id,
            "multiqc",
            "multiqc_data",
            "multiqc_data",
        ).with_suffix(FileExtensions.JSON),
    )
    write_yaml(
        content={taxprofiler_case_id: [tower_id]},
        file_path=Path(
            taxprofiler_dir,
            taxprofiler_case_id,
            "tower_ids",
        ).with_suffix(FileExtensions.YAML),
    )


@pytest.fixture(scope="function")
def taxprofiler_mock_config(taxprofiler_dir: Path, taxprofiler_case_id: str) -> None:
    """Create CSV sample sheet file for testing."""
    Path.mkdir(Path(taxprofiler_dir, taxprofiler_case_id), parents=True, exist_ok=True)
    Path(taxprofiler_dir, taxprofiler_case_id, f"{taxprofiler_case_id}_samplesheet").with_suffix(
        FileExtensions.CSV
    ).touch(exist_ok=True)


@pytest.fixture(scope="function")
def taxprofiler_deliverables_response_data(
    create_multiqc_html_file,
    create_multiqc_json_file,
    taxprofiler_case_id,
    timestamp_yesterday,
) -> InputBundle:
    return InputBundle(
        **{
            "files": [
                {
                    "path": create_multiqc_json_file.as_posix(),
                    "tags": ["multiqc-json", taxprofiler_case_id],
                },
                {
                    "path": create_multiqc_html_file.as_posix(),
                    "tags": ["multiqc-html", taxprofiler_case_id],
                },
            ],
            "created": timestamp_yesterday,
            "name": taxprofiler_case_id,
        }
    )


@pytest.fixture(scope="function")
def nf_analysis_housekeeper(
    housekeeper_api: HousekeeperAPI,
    helpers: StoreHelpers,
    mock_fastq_files: list[Path],
    sample_id: str,
    timestamp_now: datetime,
) -> HousekeeperAPI:
    """Create populated Housekeeper sample bundle mock."""

    bundle_data: dict[str, Any] = {
        "name": sample_id,
        "created": timestamp_now,
        "version": "1.0",
        "files": [
            {
                "path": fastq_file_path.as_posix(),
                "tags": [SequencingFileTag.FASTQ],
                "archive": False,
            }
            for fastq_file_path in mock_fastq_files
        ],
    }
    helpers.ensure_hk_bundle(store=housekeeper_api, bundle_data=bundle_data)
    return housekeeper_api


@pytest.fixture(scope="session")
def expected_total_reads() -> int:
    return 1_000_000


@pytest.fixture
def expected_average_q30_for_sample() -> float:
    """Return expected average Q30 for a sample."""
    return (85.5 + 80.5) / 2


@pytest.fixture
def expected_average_q30_for_flow_cell() -> float:
    return (((85.5 + 80.5) / 2) + ((83.5 + 81.5) / 2)) / 2


@pytest.fixture
def expected_total_reads_hiseq_x_flow_cell() -> int:
    """Return an expected read count"""
    return 8_000_000


@pytest.fixture
def illumina_run_encryption_service(
    cg_context: CGConfig, flow_cell_full_name: str
) -> IlluminaRunEncryptionService:
    illumina_run_encryption_service = IlluminaRunEncryptionService(
        binary_path=cg_context.encryption.binary_path,
        encryption_dir=Path(cg_context.illumina_backup_service.pdc_archiving_directory.current),
        dry_run=True,
        run_dir_data=IlluminaRunDirectoryData(
            sequencing_run_path=Path(
                cg_context.run_instruments.illumina.sequencing_runs_dir, flow_cell_full_name
            )
        ),
        pigz_binary_path=cg_context.pigz.binary_path,
        slurm_api=SlurmAPI(),
        sbatch_parameter=cg_context.illumina_backup_service.slurm_flow_cell_encryption.dict(),
        tar_api=TarAPI(binary_path=cg_context.tar.binary_path, dry_run=True),
    )
    illumina_run_encryption_service.slurm_api.set_dry_run(dry_run=True)
    return illumina_run_encryption_service


def create_process_response(
    return_code: int = 0, args: str = "", std_out: str = "", std_err: str = ""
) -> CompletedProcess:
    """Returns a CompletedProcess object with default parameters."""
    return CompletedProcess(
        args=args,
        returncode=return_code,
        stderr=std_err.encode("utf-8"),
        stdout=std_out.encode("utf-8"),
    )


# Downsample
@pytest.fixture
def store_with_case_and_sample_with_reads(
    store: Store,
    helpers: StoreHelpers,
    downsample_case_internal_id: str,
    downsample_sample_internal_id_1: str,
    downsample_sample_internal_id_2: str,
) -> Store:
    """Return a store with a case and a sample with reads."""
    case: Case = helpers.add_case(
        store=store, internal_id=downsample_case_internal_id, name=downsample_case_internal_id
    )
    order: Order = helpers.add_order(
        store=store,
        customer_id=case.customer_id,
        ticket_id=case.latest_ticket,
        order_date=case.ordered_at,
        workflow=case.data_analysis,
    )
    case.orders.append(order)
    for sample_internal_id in [downsample_sample_internal_id_1, downsample_sample_internal_id_2]:
        helpers.add_sample(
            store=store,
            customer_id=case.customer_id,
            internal_id=sample_internal_id,
            reads=100_000_000,
        )
        sample: Sample = store.get_sample_by_internal_id(internal_id=sample_internal_id)
        helpers.add_relationship(store=store, case=case, sample=sample)

    return store


@pytest.fixture
def downsample_case_internal_id() -> str:
    """Return a case internal id."""
    return "supersonicturtle"


@pytest.fixture
def downsample_sample_internal_id_1() -> str:
    """Return a sample internal id."""
    return "ACC12345675213"


@pytest.fixture
def downsample_sample_internal_id_2() -> str:
    """Return a sample internal id."""
    return "ACC12345684213"


@pytest.fixture
def number_of_reads_in_millions() -> int:
    """Return a number of reads in millions."""
    return 50


@pytest.fixture
def downsample_hk_api(
    real_housekeeper_api: HousekeeperAPI,
    fastq_file: Path,
    downsample_sample_internal_id_1: str,
    downsample_sample_internal_id_2: str,
    timestamp_yesterday: str,
    helpers: StoreHelpers,
    tmp_path_factory,
) -> HousekeeperAPI:
    """Return a Housekeeper API with a real database."""
    for sample_internal_id in [downsample_sample_internal_id_1, downsample_sample_internal_id_2]:
        tmp_fastq_file = tmp_path_factory.mktemp(f"{sample_internal_id}.fastq.gz")
        downsample_bundle: dict = {
            "name": sample_internal_id,
            "created": timestamp_yesterday,
            "expires": timestamp_yesterday,
            "files": [
                {
                    "path": tmp_fastq_file.as_posix(),
                    "archive": False,
                    "tags": [SequencingFileTag.FASTQ, sample_internal_id],
                }
            ],
        }
        helpers.ensure_hk_bundle(store=real_housekeeper_api, bundle_data=downsample_bundle)
    return real_housekeeper_api


@pytest.fixture(scope="function")
def downsample_context(
    cg_context: CGConfig,
    store_with_case_and_sample_with_reads: Store,
    downsample_hk_api: HousekeeperAPI,
) -> CGConfig:
    """Return cg context with added Store and Housekeeper API."""
    cg_context.status_db_ = store_with_case_and_sample_with_reads
    cg_context.housekeeper_api_ = downsample_hk_api
    return cg_context


@pytest.fixture
def downsample_case_name():
    return "subsonichedgehog"


@pytest.fixture
def downsample_data(
    downsample_context: CGConfig,
    downsample_sample_internal_id_1: str,
    downsample_case_internal_id: str,
    downsample_case_name: str,
    number_of_reads_in_millions: int,
) -> DownsampleData:
    return DownsampleData(
        status_db=downsample_context.status_db_,
        hk_api=downsample_context.housekeeper_api_,
        sample_id=downsample_sample_internal_id_1,
        case_id=downsample_case_internal_id,
        case_name=downsample_case_name,
        number_of_reads=number_of_reads_in_millions,
        out_dir=Path(downsample_context.downsample.downsample_dir),
    )


@pytest.fixture(scope="function")
def downsample_api(
    downsample_context: CGConfig,
) -> DownsampleAPI:
    """Return a DownsampleAPI."""
    return DownsampleAPI(
        config=downsample_context,
    )


@pytest.fixture
def fastq_file_meta_raw(flow_cell_name: str) -> dict:
    return {
        "path": Path("a", f"file{FileExtensions.FASTQ}{FileExtensions.GZIP}"),
        "lane": str(1),
        "read_direction": str(2),
        "flow_cell_id": flow_cell_name,
        "undetermined": None,
    }


@pytest.fixture()
def illumina_metrics_service() -> IlluminaDataTransferService:
    return IlluminaDataTransferService()


@pytest.fixture
def completed_status_summary():
    return StatusSummary(count=1, case_ids=["completed_case_id"])


@pytest.fixture
def delivered_status_summary():
    return StatusSummary(count=1, case_ids=["delivered_case_id"])


@pytest.fixture
def failed_status_summary():
    return StatusSummary(count=1, case_ids=["failed_case_id"])


@pytest.fixture
def empty_status_summary():
    return StatusSummary()


@pytest.fixture
def analysis_summary(
    empty_status_summary: StatusSummary,
    completed_status_summary: StatusSummary,
    delivered_status_summary: StatusSummary,
    failed_status_summary: StatusSummary,
):
    return AnalysisSummary(
        order_id=1,
        cancelled=empty_status_summary,
        completed=completed_status_summary,
        running=empty_status_summary,
        delivered=delivered_status_summary,
        failed=failed_status_summary,
    )


@pytest.fixture
def lims_case(fixtures_dir: Path) -> dict:
    """Returns a LIMS case dict of samples."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(fixtures_dir, "report", "lims_family.json")
    )


@pytest.fixture
def lims_samples(lims_case: dict) -> list[dict]:
    """Returns the samples of a LIMS case."""
    return lims_case["samples"]


@pytest.fixture
def library_prep_method() -> str:
    return "Manual TruSeq DNA PCR-free library preparation (9.33.15)"


@pytest.fixture
def libary_sequencing_method() -> str:
    return "NovaSeq X sequencing method (9.33.15)"


@pytest.fixture
def capture_kit() -> str:
    return "panel.bed"
