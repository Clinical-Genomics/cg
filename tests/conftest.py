"""
    Conftest file for pytest fixtures that needs to be shared for multiple tests
"""
import copy
import datetime as dt
import json
import logging
import os
import pytest
import shutil

from pathlib import Path
from typing import Generator


from cg.apps.gt import GenotypeAPI
from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Pipeline
from cg.constants.priority import SlurmQos
from cg.meta.orders.external_data import ExternalDataAPI
from cg.meta.rsync import RsyncAPI
from cg.models import CompressionData
from cg.models.cg_config import CGConfig
from cg.models.observations.observations_input_files import ObservationsInputFiles
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

LOG = logging.getLogger(__name__)


# Case fixtures


@pytest.fixture(name="slurm_account")
def fixture_slurm_account() -> str:
    return "super_account"


@pytest.fixture(name="user_name")
def fixture_user_name() -> str:
    return "Paul Anderson"


@pytest.fixture(name="user_mail")
def fixture_user_mail() -> str:
    return "paul@magnolia.com"


@pytest.fixture(name="email_adress")
def fixture_email_adress() -> str:
    return "james.holden@scilifelab.se"


@pytest.fixture(name="case_id")
def fixture_case_id() -> str:
    """Return a case id"""
    return "yellowhog"


@pytest.fixture(name="sample_id")
def fixture_sample_id() -> str:
    """Returns a sample id"""
    return "ADM1"


@pytest.fixture(name="cust_sample_id")
def fixture_cust_sample_id() -> str:
    """Returns a customer sample id"""
    return "child"


@pytest.fixture(name="family_name")
def fixture_family_name() -> str:
    """Return a case name"""
    return "case"


@pytest.fixture(name="customer_id")
def fixture_customer_id() -> str:
    """Return a customer id"""
    return "cust000"


@pytest.fixture(name="ticket_nr")
def fixture_ticket_nr() -> int:
    """Return a ticket nr"""
    return 123456


@pytest.fixture(scope="function", name="analysis_family_single_case")
def fixture_analysis_family_single(case_id: str, family_name: str, ticket_nr: int) -> dict:
    """Build an example case."""
    return {
        "name": family_name,
        "internal_id": case_id,
        "data_analysis": str(Pipeline.MIP_DNA),
        "application_type": "wgs",
        "panels": ["IEM", "EP"],
        "samples": [
            {
                "name": "proband",
                "sex": "male",
                "internal_id": "ADM1",
                "status": "affected",
                "ticket_number": ticket_nr,
                "reads": 5000000000,
                "capture_kit": "GMSmyeloid",
            }
        ],
    }


@pytest.fixture(scope="function", name="analysis_family")
def fixture_analysis_family(case_id: str, family_name: str, ticket_nr: int) -> dict:
    """Return a dictionary with information from a analysis case"""
    return {
        "name": family_name,
        "internal_id": case_id,
        "data_analysis": str(Pipeline.MIP_DNA),
        "application_type": "wgs",
        "panels": ["IEM", "EP"],
        "samples": [
            {
                "name": "child",
                "sex": "male",
                "internal_id": "ADM1",
                "father": "ADM2",
                "mother": "ADM3",
                "status": "affected",
                "ticket_number": ticket_nr,
                "reads": 5000000,
                "capture_kit": "GMSmyeloid",
            },
            {
                "name": "father",
                "sex": "male",
                "internal_id": "ADM2",
                "status": "unaffected",
                "ticket_number": ticket_nr,
                "reads": 6000000,
                "capture_kit": "GMSmyeloid",
            },
            {
                "name": "mother",
                "sex": "female",
                "internal_id": "ADM3",
                "status": "unaffected",
                "ticket_number": ticket_nr,
                "reads": 7000000,
                "capture_kit": "GMSmyeloid",
            },
        ],
    }


# Config fixtures


@pytest.fixture(name="base_config_dict")
def fixture_base_config_dict() -> dict:
    """Returns the basic configs necessary for running CG"""
    return {
        "database": "sqlite:///",
        "madeline_exe": "path/to/madeline",
        "bed_path": "path/to/bed",
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
    }


@pytest.fixture(name="cg_config_object")
def fixture_cg_config_object(base_config_dict: dict) -> CGConfig:
    """Return a CG config dict"""
    return CGConfig(**base_config_dict)


@pytest.fixture
def chanjo_config_dict() -> dict:
    """Chanjo configs"""
    return {"chanjo": {"config_path": "chanjo_config", "binary_path": "chanjo"}}


@pytest.fixture
def crunchy_config_dict():
    """Crunchy configs"""
    return {
        "crunchy": {
            "cram_reference": "/path/to/fasta",
            "slurm": {"account": "mock_account", "mail_user": "mock_mail", "conda_env": "mock_env"},
        }
    }


@pytest.fixture(name="hk_config_dict")
def fixture_hk_config_dict(root_path):
    """Crunchy configs"""
    return {
        "housekeeper": {
            "database": "sqlite:///:memory:",
            "root": str(root_path),
        }
    }


@pytest.fixture(name="genotype_config")
def fixture_genotype_config() -> dict:
    """
    genotype config fixture
    """
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
    """RsyncAPI fixture"""
    _rsync_api: RsyncAPI = RsyncAPI(config=cg_context)
    return _rsync_api


@pytest.fixture(name="external_data_api")
def fixture_external_data_api(cg_context: CGConfig) -> ExternalDataAPI:
    """ExternalDataAPI fixture"""
    _external_data_api: ExternalDataAPI = ExternalDataAPI(config=cg_context)
    return _external_data_api


@pytest.fixture(name="genotype_api")
def fixture_genotype_api(genotype_config: dict) -> GenotypeAPI:
    """
    genotype API fixture
    """
    _genotype_api = GenotypeAPI(genotype_config)
    _genotype_api.set_dry_run(True)
    return _genotype_api


@pytest.fixture(scope="function")
def madeline_api(madeline_output) -> MockMadelineAPI:
    """madeline_api fixture"""
    _api = MockMadelineAPI()
    _api.set_outpath(madeline_output)

    return _api


@pytest.fixture(name="ticket_number")
def fixture_ticket_number() -> int:
    """Return a ticket number for testing"""
    return 123456


@pytest.fixture(name="osticket")
def fixture_os_ticket(ticket_number: int) -> MockOsTicket:
    """Return a api that mock the os ticket api"""
    api = MockOsTicket()
    api.set_ticket_nr(ticket_number)
    return api


# Files fixtures

# Common file fixtures
@pytest.fixture(name="fixtures_dir")
def fixture_fixtures_dir() -> Path:
    """Return the path to the fixtures dir"""
    return Path("tests/fixtures")


@pytest.fixture(name="analysis_dir")
def fixture_analysis_dir(fixtures_dir: Path) -> Path:
    """Return the path to the analysis dir"""
    return fixtures_dir / "analysis"


@pytest.fixture(name="apps_dir")
def fixture_apps_dir(fixtures_dir: Path) -> Path:
    """Return the path to the apps dir"""
    return fixtures_dir / "apps"


@pytest.fixture(name="fastq_dir")
def fixture_fastq_dir(fixtures_dir: Path) -> Path:
    """Return the path to the fastq files dir"""
    return fixtures_dir / "fastq"


@pytest.fixture(scope="function", name="project_dir")
def fixture_project_dir(
    tmpdir_factory,
) -> Generator[Path, None, None]:
    """Path to a temporary directory where intermediate files can be stored"""
    my_tmpdir: Path = Path(tmpdir_factory.mktemp("data"))
    yield my_tmpdir


@pytest.fixture(scope="function")
def tmp_file(project_dir):
    """Get a temp file"""
    return project_dir / "test"


@pytest.fixture(name="non_existing_file_path")
def fixture_non_existing_file_path(project_dir: Path) -> Path:
    """Return the path to a non existing file"""
    return project_dir / "a_file.txt"


@pytest.fixture(name="content")
def fixture_content() -> str:
    """Return some content for a file"""
    _content = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt"
        " ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ull"
        "amco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehende"
        "rit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaec"
        "at cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
    )
    return _content


@pytest.fixture(name="filled_file")
def fixture_filled_file(non_existing_file_path: Path, content: str) -> Path:
    """Return the path to a existing file with some content"""
    with open(non_existing_file_path, "w") as outfile:
        outfile.write(content)
    return non_existing_file_path


@pytest.fixture(name="orderforms")
def fixture_orderform(fixtures_dir: Path) -> Path:
    """Return the path to the directory with orderforms"""
    return fixtures_dir / "orderforms"


@pytest.fixture(name="case_qc_sample_info_path")
def fixture_case_qc_sample_info_path(fixtures_dir) -> Path:
    """Return path to case_qc_sample_info.yaml"""
    return Path(fixtures_dir, "apps", "mip", "dna", "store", "case_qc_sample_info.yaml")


@pytest.fixture(name="case_qc_metrics_deliverables")
def fixture_case_qc_metrics_deliverables(apps_dir: Path) -> Path:
    """Return the path to a qc metrics deliverables file with case data"""
    return Path("tests", "fixtures", "apps", "mip", "case_metrics_deliverables.yaml")


@pytest.fixture(name="mip_dna_store_files")
def fixture_mip_dna_store_files(apps_dir: Path) -> Path:
    """Return the path to the directory with mip dna store files"""
    return apps_dir / "mip" / "dna" / "store"


@pytest.fixture(name="mip_analysis_dir")
def fixture_mip_analysis_dir(analysis_dir: Path) -> Path:
    """Return the path to the directory with mip analysis files"""
    return analysis_dir / "mip"


@pytest.fixture(name="balsamic_analysis_dir")
def fixture_balsamic_analysis_dir(analysis_dir: Path) -> Path:
    """Return the path to the directory with balsamic analysis files"""
    return analysis_dir / "balsamic"


@pytest.fixture(name="balsamic_panel_analysis_dir")
def fixture_balsamic_panel_analysis_dir(balsamic_analysis_dir: Path) -> Path:
    """Return the path to the directory with balsamic analysis files"""
    return balsamic_analysis_dir / "tn_panel"


@pytest.fixture(name="mip_dna_analysis_dir")
def fixture_mip_dna_analysis_dir(mip_analysis_dir: Path) -> Path:
    """Return the path to the directory with mip dna analysis files"""
    return mip_analysis_dir / "dna"


@pytest.fixture(name="sample1_cram")
def fixture_sample1_cram(mip_dna_analysis_dir: Path) -> Path:
    """Return the path to the cram file for sample 1"""
    return mip_dna_analysis_dir / "adm1.cram"


@pytest.fixture(name="mip_deliverables_file")
def fixture_mip_deliverables_files(mip_dna_store_files: Path) -> Path:
    """Fixture for general deliverables file in mip"""
    return mip_dna_store_files / "case_id_deliverables.yaml"


@pytest.fixture(name="vcf_file")
def fixture_vcf_file(mip_dna_store_files: Path) -> Path:
    """Return the path to to a vcf file"""
    return mip_dna_store_files / "yellowhog_clinical_selected.vcf"


@pytest.fixture(name="fastq_file")
def fixture_fastq_file(fastq_dir: Path) -> Path:
    """Return the path to to a fastq file"""
    return fastq_dir / "dummy_run_R1_001.fastq.gz"


# Orderform fixtures


@pytest.fixture
def microbial_orderform(orderforms: Path) -> str:
    """Orderform fixture for microbial samples"""
    return Path(orderforms / "1603.10.microbial.xlsx").as_posix()


@pytest.fixture
def sarscov2_orderform(orderforms: Path) -> str:
    """Orderform fixture for sarscov2 samples"""
    return Path(orderforms / "2184.5.sarscov2.xlsx").as_posix()


@pytest.fixture
def rml_orderform(orderforms: Path) -> str:
    """Orderform fixture for RML samples"""
    return Path(orderforms / "1604.10.rml.xlsx").as_posix()


@pytest.fixture
def mip_json_orderform(orderforms: Path) -> dict:
    """Load an example of json scout order."""
    return json.load(open(orderforms / "mip-json.json"))


@pytest.fixture(name="madeline_output")
def fixture_madeline_output(apps_dir: Path) -> str:
    """File with madeline output"""
    _file = apps_dir / "madeline/madeline.xml"
    return str(_file)


@pytest.fixture
def mip_order_to_submit() -> dict:
    """Load an example scout order."""
    return json.load(open("tests/fixtures/cgweb_orders/mip.json"))


@pytest.fixture
def mip_rna_order_to_submit() -> dict:
    """Load an example rna order."""
    return json.load(open("tests/fixtures/cgweb_orders/mip_rna.json"))


@pytest.fixture
def external_order_to_submit() -> dict:
    """Load an example external order."""
    return json.load(open("tests/fixtures/cgweb_orders/external.json"))


@pytest.fixture
def fastq_order_to_submit() -> dict:
    """Load an example fastq order."""
    return json.load(open("tests/fixtures/cgweb_orders/fastq.json"))


@pytest.fixture
def rml_order_to_submit() -> dict:
    """Load an example rml order."""
    return json.load(open("tests/fixtures/cgweb_orders/rml.json"))


@pytest.fixture
def metagenome_order_to_submit() -> dict:
    """Load an example metagenome order."""
    return json.load(open("tests/fixtures/cgweb_orders/metagenome.json"))


@pytest.fixture
def microbial_order_to_submit() -> dict:
    """Load an example microbial order."""
    return json.load(open("tests/fixtures/cgweb_orders/microsalt.json"))


@pytest.fixture
def sarscov2_order_to_submit() -> dict:
    """Load an example sarscov2 order."""
    return json.load(open("tests/fixtures/cgweb_orders/sarscov2.json"))


@pytest.fixture
def balsamic_order_to_submit() -> dict:
    """Load an example cancer order."""
    return json.load(open("tests/fixtures/cgweb_orders/balsamic.json"))


# Compression fixtures


@pytest.fixture(scope="function", name="run_name")
def fixture_run_name() -> str:
    """Return the name of a fastq run"""
    return "fastq_run"


@pytest.fixture(scope="function", name="original_fastq_data")
def fixture_original_fastq_data(fastq_dir: Path, run_name) -> CompressionData:
    """Return a compression object with a path to the original fastq files"""

    return CompressionData(fastq_dir / run_name)


@pytest.fixture(scope="function", name="fastq_stub")
def fixture_fastq_stub(project_dir: Path, run_name: str) -> Path:
    """Creates a path to the base format of a fastq run"""
    return project_dir / run_name


@pytest.fixture(scope="function", name="compression_object")
def fixture_compression_object(
    fastq_stub: Path, original_fastq_data: CompressionData
) -> CompressionData:
    """Creates compression data object with information about files used in fastq compression"""
    working_files = CompressionData(fastq_stub)
    shutil.copy(str(original_fastq_data.fastq_first), str(working_files.fastq_first))
    shutil.copy(str(original_fastq_data.fastq_second), str(working_files.fastq_second))
    return working_files


# Unknown file fixtures


@pytest.fixture(name="bcf_file")
def fixture_bcf_file(apps_dir: Path) -> Path:
    """Return the path to a bcf file"""
    return apps_dir / "gt" / "yellowhog.bcf"


@pytest.fixture(scope="function", name="bed_file")
def fixture_bed_file(analysis_dir) -> str:
    """Get the path to a bed file file"""
    return str(analysis_dir / "sample_coverage.bed")


# Helper fixtures


@pytest.fixture(name="helpers")
def fixture_helpers():
    """Return a class with helper functions for the stores"""
    return StoreHelpers()


@pytest.fixture(name="small_helpers")
def fixture_small_helpers():
    """Return a class with small helper functions"""
    return SmallHelpers()


# HK fixtures


@pytest.fixture(name="root_path")
def fixture_root_path(project_dir: Path) -> Path:
    """Return the path to a hk bundles dir"""
    _root_path = project_dir / "bundles"
    _root_path.mkdir(parents=True, exist_ok=True)
    return _root_path


@pytest.fixture(scope="function", name="timestamp")
def fixture_timestamp() -> dt.datetime:
    """Return a time stamp in date time format"""
    return dt.datetime(2020, 5, 1)


@pytest.fixture(scope="function", name="later_timestamp")
def fixture_later_timestamp() -> dt.datetime:
    """Return a time stamp in date time format"""
    return dt.datetime(2020, 6, 1)


@pytest.fixture(scope="function", name="timestamp_today")
def fixture_timestamp_today() -> dt.datetime:
    """Return a time stamp of todays date in date time format"""
    return dt.datetime.now()


@pytest.fixture(scope="function", name="timestamp_yesterday")
def fixture_timestamp_yesterday(timestamp_today: dt.datetime) -> dt.datetime:
    """Return a time stamp of yesterdays date in date time format"""
    return timestamp_today - dt.timedelta(days=1)


@pytest.fixture(scope="function", name="timestamp_in_2_weeks")
def fixture_timestamp_in_2_weeks(timestamp_today: dt.datetime) -> dt.datetime:
    """Return a time stamp 14 days ahead in time"""
    return timestamp_today + dt.timedelta(days=14)


@pytest.fixture(scope="function", name="hk_bundle_data")
def fixture_hk_bundle_data(case_id: str, bed_file: str, timestamp: dt.datetime) -> dict:
    """Get some bundle data for housekeeper"""
    return {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [{"path": bed_file, "archive": False, "tags": ["bed", "sample"]}],
    }


@pytest.fixture(scope="function", name="sample_hk_bundle_no_files")
def fixture_sample_hk_bundle_no_files(sample_id: str, timestamp: dt.datetime) -> dict:
    """Create a complete bundle mock for testing compression"""
    return {
        "name": sample_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [],
    }


@pytest.fixture(scope="function", name="case_hk_bundle_no_files")
def fixture_case_hk_bundle_no_files(case_id: str, timestamp: dt.datetime) -> dict:
    """Create a complete bundle mock for testing compression"""
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
    """
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
) -> MockHousekeeperAPI:
    """Get a housekeeper version object"""
    return helpers.ensure_hk_version(housekeeper_api, hk_bundle_data)


# Process Mock


@pytest.fixture(name="sbatch_job_number")
def fixture_sbatch_job_number() -> int:
    return 123456


@pytest.fixture(name="process")
def fixture_process() -> ProcessMock:
    """Returns a mocked process"""
    return ProcessMock()


# Hermes mock


@pytest.fixture(name="hermes_process")
def fixture_hermes_process() -> ProcessMock:
    """Return a mocked hermes process"""
    return ProcessMock(binary="hermes")


@pytest.fixture(name="hermes_api")
def fixture_hermes_api(hermes_process: ProcessMock) -> HermesApi:
    """Return a hermes api with a mocked process"""
    hermes_config = {"hermes": {"deploy_config": "deploy_config", "binary_path": "/bin/true"}}
    hermes_api = HermesApi(config=hermes_config)
    hermes_api.process = hermes_process
    return hermes_api


# Scout fixtures


@pytest.fixture(scope="function", name="scout_api")
def fixture_scout_api() -> MockScoutAPI:
    """Setup Scout api."""
    return MockScoutAPI()


# Crunchy fixtures


@pytest.fixture(scope="function", name="crunchy_api")
def fixture_crunchy_api():
    """Setup Crunchy api."""
    return MockCrunchyAPI()


# Store fixtures


@pytest.fixture(scope="function", name="analysis_store")
def fixture_analysis_store(
    base_store: Store, analysis_family: dict, wgs_application_tag: str, helpers
):
    """Setup a store instance for testing analysis API."""
    helpers.ensure_case_from_dict(
        base_store, case_info=analysis_family, app_tag=wgs_application_tag
    )

    yield base_store


@pytest.fixture(scope="function", name="analysis_store_trio")
def fixture_analysis_store_trio(analysis_store):
    """Setup a store instance with a trion loaded for testing analysis API."""

    yield analysis_store


@pytest.fixture(scope="function", name="analysis_store_single_case")
def fixture_analysis_store_single(base_store, analysis_family_single_case, helpers):
    """Setup a store instance with a single ind case for testing analysis API."""
    helpers.ensure_case_from_dict(base_store, case_info=analysis_family_single_case)

    yield base_store


@pytest.fixture(scope="function", name="customer_group")
def fixture_customer_group() -> str:
    """Return a default customer group"""
    return "all_customers"


@pytest.fixture(scope="function", name="customer_production")
def fixture_customer_production(customer_group) -> dict:
    """Return a dictionary with information about the prod customer"""
    return dict(
        customer_id="cust000",
        name="Production",
        scout_access=True,
        customer_group=customer_group,
    )


@pytest.fixture(scope="function", name="external_wgs_application_tag")
def fixture_external_wgs_application_tag() -> str:
    """Return the external wgs app tag"""
    return "WGXCUSC000"


@pytest.fixture(scope="function", name="external_wgs_info")
def fixture_external_wgs_info(external_wgs_application_tag) -> dict:
    """Return a dictionary with information external WGS application"""
    return dict(
        application_tag=external_wgs_application_tag,
        application_type="wgs",
        description="External WGS",
        is_external=True,
        target_reads=10,
    )


@pytest.fixture(scope="function", name="external_wes_application_tag")
def fixture_external_wes_application_tag() -> str:
    """Return the external whole exome sequencing app tag"""
    return "EXXCUSR000"


@pytest.fixture(scope="function", name="external_wes_info")
def fixture_external_wes_info(external_wes_application_tag) -> dict:
    """Return a dictionary with information external WES application"""
    return dict(
        application_tag=external_wes_application_tag,
        application_type="wes",
        description="External WES",
        is_external=True,
        target_reads=10,
    )


@pytest.fixture(scope="function", name="wgs_application_tag")
def fixture_wgs_application_tag() -> str:
    """Return the wgs app tag"""
    return "WGSPCFC060"


@pytest.fixture(scope="function", name="wgs_application_info")
def fixture_wgs_application_info(wgs_application_tag) -> dict:
    """Return a dictionary with information the WGS application"""
    return dict(
        application_tag=wgs_application_tag,
        application_type="wgs",
        description="WGS, double",
        sequencing_depth=30,
        is_external=True,
        is_accredited=True,
        target_reads=10,
    )


@pytest.fixture(name="store")
def fixture_store() -> Store:
    """Fixture with a CG store"""
    _store = Store(uri="sqlite:///")
    _store.create_all()
    yield _store
    _store.drop_all()


@pytest.fixture(name="apptag_rna")
def fixture_apptag_rna() -> str:
    return "RNAPOAR025"


@pytest.fixture(scope="function", name="base_store")
def fixture_base_store(store: Store, apptag_rna: str) -> Store:
    """Setup and example store."""
    customer_group = store.add_customer_group("all_customers", "all customers")

    store.add_commit(customer_group)
    customers = [
        store.add_customer(
            "cust000",
            "Production",
            scout_access=True,
            customer_group=customer_group,
            invoice_address="Test street",
            invoice_reference="ABCDEF",
        ),
        store.add_customer(
            "cust001",
            "Customer",
            scout_access=False,
            customer_group=customer_group,
            invoice_address="Test street",
            invoice_reference="ABCDEF",
        ),
        store.add_customer(
            "cust002",
            "Karolinska",
            scout_access=True,
            customer_group=customer_group,
            invoice_address="Test street",
            invoice_reference="ABCDEF",
        ),
        store.add_customer(
            "cust003",
            "CMMS",
            scout_access=True,
            customer_group=customer_group,
            invoice_address="Test street",
            invoice_reference="ABCDEF",
        ),
    ]
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
            tag="RMLS05R150",
            category="rml",
            description="Ready-made",
            sequencing_depth=0,
            percent_kth=80,
            percent_reads_guaranteed=75,
            target_reads=10,
        ),
        store.add_application(
            tag="WGTPCFC030",
            category="wgs",
            description="WGS trio",
            is_accredited=True,
            sequencing_depth=30,
            target_reads=30,
            limitations="some",
            percent_kth=80,
            percent_reads_guaranteed=75,
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
def sample_store(base_store) -> Store:
    """Populate store with samples."""
    new_samples = [
        base_store.add_sample("ordered", sex="male"),
        base_store.add_sample("received", sex="unknown", received=dt.datetime.now()),
        base_store.add_sample(
            "received-prepared",
            sex="unknown",
            received=dt.datetime.now(),
            prepared_at=dt.datetime.now(),
        ),
        base_store.add_sample("external", sex="female", external=True),
        base_store.add_sample(
            "external-received", sex="female", external=True, received=dt.datetime.now()
        ),
        base_store.add_sample(
            "sequenced",
            sex="male",
            received=dt.datetime.now(),
            prepared_at=dt.datetime.now(),
            sequenced_at=dt.datetime.now(),
            reads=(310 * 1000000),
        ),
        base_store.add_sample(
            "sequenced-partly",
            sex="male",
            received=dt.datetime.now(),
            prepared_at=dt.datetime.now(),
            reads=(250 * 1000000),
        ),
    ]
    customer = base_store.customers().first()
    external_app = base_store.application("WGXCUSC000").versions[0]
    wgs_app = base_store.application("WGTPCFC030").versions[0]
    for sample in new_samples:
        sample.customer = customer
        sample.application_version = external_app if "external" in sample.name else wgs_app
    base_store.add_commit(new_samples)
    return base_store


@pytest.fixture(scope="function", name="trailblazer_api")
def fixture_trailblazer_api() -> MockTB:
    return MockTB()


@pytest.fixture(scope="function", name="lims_api")
def fixture_lims_api() -> MockLimsAPI:
    return MockLimsAPI()


@pytest.fixture(name="config_root_dir")
def config_root_dir(tmpdir_factory):
    return Path("tests/fixtures/data")


@pytest.fixture()
def housekeeper_dir(tmpdir_factory):
    return tmpdir_factory.mktemp("housekeeper")


@pytest.fixture()
def mip_dir(tmpdir_factory):
    return tmpdir_factory.mktemp("mip")


@pytest.fixture(scope="function")
def fluffy_dir(tmpdir_factory):
    return tmpdir_factory.mktemp("fluffy")


@pytest.fixture(scope="function")
def balsamic_dir(tmpdir_factory):
    return tmpdir_factory.mktemp("balsamic")


@pytest.fixture(scope="function")
def cg_dir(tmpdir_factory):
    return tmpdir_factory.mktemp("cg")


@pytest.fixture(scope="function")
def microsalt_dir(tmpdir_factory):
    return tmpdir_factory.mktemp("microsalt")


@pytest.fixture(name="fixture_cg_uri")
def fixture_cg_uri() -> str:
    return "sqlite:///"


@pytest.fixture(name="fixture_hk_uri")
def fixture_hk_uri() -> str:
    return "sqlite:///"


@pytest.fixture(name="context_config")
def fixture_context_config(
    fixture_cg_uri: str,
    fixture_hk_uri: str,
    fluffy_dir: str,
    housekeeper_dir: str,
    mip_dir: str,
    cg_dir: str,
    balsamic_dir: str,
    microsalt_dir: str,
) -> dict:
    return {
        "database": fixture_cg_uri,
        "madeline_exe": "echo",
        "bed_path": str(cg_dir),
        "delivery_path": str(cg_dir),
        "hermes": {"deploy_config": "hermes-deploy-stage.yaml", "binary_path": "hermes"},
        "email_base_settings": {
            "sll_port": 465,
            "smtp_server": "smtp.gmail.com",
            "sender_email": "test@gmail.com",
            "sender_password": "",
        },
        "demultiplex": {
            "run_dir": "tests/fixtures/apps/demultiplexing/flowcell-runs",
            "out_dir": "tests/fixtures/apps/demultiplexing/demultiplexed-runs",
            "slurm": {
                "account": "development",
                "mail_user": "mans.magnusson@scilifelab.se",
            },
        },
        "fluffy": {
            "deploy_config": "fluffy-deploy-stage.yaml",
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
        "statina": {"host": "http://localhost:28002"},
        "data-delivery": {
            "destination_path": "server.name.se:/some",
            "covid_destination_path": "server.name.se:/another/%s/foldername/",
            "covid_report_path": "/folder_structure/%s/yet_another_folder/filename_%s_data_*.csv",
            "base_path": "/another/path",
            "account": "development",
            "mail_user": "an@email.com",
        },
        "external": {
            "hasta": "/path/on/hasta/%s",
            "caesar": "server.name.se:/path/%s/on/caesar",
        },
        "shipping": {"host_config": "host_config_stage.yaml", "binary_path": "echo"},
        "housekeeper": {"database": fixture_hk_uri, "root": str(housekeeper_dir)},
        "trailblazer": {
            "service_account": "SERVICE",
            "service_account_auth_file": "trailblazer-auth.json",
            "host": "https://trailblazer.scilifelab.se/",
        },
        "gisaid": {
            "binary_path": "/path/to/gisaid_uploader.py",
            "log_dir": "/path/to/log",
            "submitter": "s.submitter",
            "logwatch_email": "some@email.com",
            "upload_password": "pass",
            "upload_cid": "cid",
        },
        "lims": {
            "host": "https://lims.scilifelab.se",
            "username": "user",
            "password": "password",
        },
        "chanjo": {"binary_path": "echo", "config_path": "chanjo-stage.yaml"},
        "genotype": {
            "binary_path": "echo",
            "config_path": "genotype-stage.yaml",
        },
        "vogue": {"binary_path": "echo", "config_path": "vogue-stage.yaml"},
        "cgstats": {"database": "sqlite:///./cgstats", "root": str(cg_dir)},
        "scout": {
            "binary_path": "echo",
            "config_path": "scout-stage.yaml",
            "deploy_config": "scout-deploy-stage.yaml",
        },
        "loqusdb": {"binary_path": "loqusdb", "config_path": "loqusdb-stage.yaml"},
        "loqusdb-wes": {"binary_path": "loqusdb", "config_path": "loqusdb-wes-stage.yaml"},
        "balsamic": {
            "root": str(balsamic_dir),
            "binary_path": "echo",
            "conda_env": "S_BALSAMIC",
            "balsamic_cache": "hello",
            "slurm": {
                "mail_user": "test.email@scilifelab.se",
                "account": "development",
                "qos": SlurmQos.LOW,
            },
        },
        "microsalt": {
            "root": str(microsalt_dir),
            "queries_path": Path(microsalt_dir, "queries").as_posix(),
            "binary_path": "echo",
            "conda_env": "S_microSALT",
        },
        "mip-rd-dna": {
            "conda_env": "S_mip9.0",
            "mip_config": "mip9.0-dna-stage.yaml",
            "pipeline": "analyse rd_dna",
            "root": str(mip_dir),
            "script": "mip",
        },
        "mip-rd-rna": {
            "conda_env": "S_mip9.0",
            "mip_config": "mip9.0-rna-stage.yaml",
            "pipeline": "analyse rd_rna",
            "root": str(mip_dir),
            "script": "mip",
        },
        "mutacc-auto": {
            "config_path": "mutacc-auto-stage.yaml",
            "binary_path": "echo",
            "padding": 300,
        },
        "mutant": {
            "binary_path": "echo",
            "conda_env": "S_mutant",
            "root": str(mip_dir),
        },
        "crunchy": {
            "cram_reference": "grch37_homo_sapiens_-d5-.fasta",
            "slurm": {
                "account": "development",
                "mail_user": "mans.magnusson@scilifelab.se",
                "conda_env": "S_crunchy",
            },
        },
        "backup": {"root": {"hiseqx": "flowcells/hiseqx", "hiseqga": "RUNS/", "novaseq": "runs/"}},
    }


@pytest.fixture(name="cg_context")
def fixture_cg_context(
    context_config: dict, base_store: Store, housekeeper_api: HousekeeperAPI
) -> CGConfig:
    cg_config = CGConfig(**context_config)
    cg_config.status_db_ = base_store
    cg_config.housekeeper_api_ = housekeeper_api
    return cg_config


@pytest.fixture(name="observation_input_files_raw")
def fixture_observation_input_files_raw(case_id: str, filled_file: Path) -> dict:
    """Raw observations input files"""
    return {
        "case_id": case_id,
        "pedigree": filled_file,
        "snv_gbcf": filled_file,
        "snv_vcf": filled_file,
        "sv_vcf": None,
    }
