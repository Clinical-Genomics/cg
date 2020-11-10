"""
    Conftest file for pytest fixtures that needs to be shared for multiple tests
"""
import copy
import datetime as dt
import logging
import shutil
import os
from pathlib import Path

import pytest
import ruamel.yaml

from cg.apps.hk import HousekeeperAPI
from cg.apps.mip import parse_sampleinfo, parse_qcmetrics
from cg.apps.gt import GenotypeAPI
from cg.models import CompressionData
from cg.store import Store

from .mocks.crunchy import MockCrunchyAPI
from .mocks.hk_mock import MockHousekeeperAPI
from .mocks.madeline import MockMadelineAPI
from .mocks.scout import MockScoutAPI
from .small_helpers import SmallHelpers
from .store_helpers import StoreHelpers
from .mocks.tb_mock import MockTB

CHANJO_CONFIG = {"chanjo": {"config_path": "chanjo_config", "binary_path": "chanjo"}}
CRUNCHY_CONFIG = {
    "crunchy": {
        "cram_reference": "/path/to/fasta",
        "slurm": {"account": "mock_account", "mail_user": "mock_mail", "conda_env": "mock_env"},
    }
}


LOG = logging.getLogger(__name__)

# Case fixtures


@pytest.fixture(name="case_id")
def fixture_case_id():
    """Return a case id"""
    return "yellowhog"


@pytest.yield_fixture(scope="function", name="family_name")
def fixture_family_name() -> str:
    """Return a family name"""
    return "family"


@pytest.fixture(scope="function", name="analysis_family_single_case")
def fixture_analysis_family_single(case_id, family_name):
    """Build an example family."""
    family = {
        "name": family_name,
        "internal_id": case_id,
        "data_analysis": "mip",
        "application_type": "wgs",
        "panels": ["IEM", "EP"],
        "samples": [
            {
                "name": "proband",
                "sex": "male",
                "internal_id": "ADM1",
                "status": "affected",
                "ticket_number": 123456,
                "reads": 5000000000,
                "capture_kit": "GMSmyeloid",
            }
        ],
    }
    return family


@pytest.yield_fixture(scope="function", name="analysis_family")
def fixture_analysis_family(case_id, family_name) -> dict:
    """Return a dictionary with information from a analysis family"""
    family = {
        "name": family_name,
        "internal_id": case_id,
        "data_analysis": "mip",
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
                "ticket_number": 123456,
                "reads": 5000000,
                "capture_kit": "GMSmyeloid",
            },
            {
                "name": "father",
                "sex": "male",
                "internal_id": "ADM2",
                "status": "unaffected",
                "ticket_number": 123456,
                "reads": 6000000,
                "capture_kit": "GMSmyeloid",
            },
            {
                "name": "mother",
                "sex": "female",
                "internal_id": "ADM3",
                "status": "unaffected",
                "ticket_number": 123456,
                "reads": 7000000,
                "capture_kit": "GMSmyeloid",
            },
        ],
    }

    return family


# Config fixtures


@pytest.fixture
def chanjo_config_dict():
    """Chanjo configs"""
    _config = dict()
    _config.update(CHANJO_CONFIG)
    return _config


@pytest.fixture
def crunchy_config_dict():
    """Crunchy configs"""
    _config = dict()
    _config.update(CRUNCHY_CONFIG)
    return _config


@pytest.fixture(name="hk_config_dict")
def fixture_hk_config_dict(root_path):
    """Crunchy configs"""
    _config = {"housekeeper": {"database": "sqlite:///:memory:", "root": str(root_path)}}
    return _config


@pytest.fixture(name="genotype_config")
def fixture_genotype_config() -> dict:
    """
    genotype config fixture
    """
    _config = {
        "genotype": {
            "database": "database",
            "config_path": "config/path",
            "binary_path": "gtdb",
        }
    }
    return _config


# Api fixtures


@pytest.fixture(name="genotype_api")
def fixture_genotype_api(genotype_config: dict) -> GenotypeAPI:
    """
    genotype API fixture
    """
    _genotype_api = GenotypeAPI(genotype_config)
    _genotype_api.set_dry_run(True)
    return _genotype_api


@pytest.yield_fixture(scope="function")
def madeline_api(madeline_output):
    """madeline_api fixture"""
    _api = MockMadelineAPI()
    _api.set_outpath(madeline_output)

    yield _api


# Files fixtures

# Common file fixtures
@pytest.fixture(name="fixtures_dir")
def fixture_fixtures_dir() -> Path:
    """Return the path to the fixtures dir"""
    return Path("tests/fixtures")


@pytest.fixture(name="analysis_dir")
def fixture_analysis_dir(fixtures_dir) -> Path:
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
def fixture_project_dir(tmpdir_factory):
    """Path to a temporary directory where intermediate files can be stored"""
    my_tmpdir = Path(tmpdir_factory.mktemp("data"))
    yield my_tmpdir
    shutil.rmtree(str(my_tmpdir))


@pytest.fixture(scope="function")
def tmp_file(project_dir):
    """Get a temp file"""
    return project_dir / "test"


@pytest.fixture(name="orderforms")
def fixture_orderform(fixtures_dir: Path) -> Path:
    """Return the path to the directory with orderforms"""
    _path = fixtures_dir / "orderforms"
    return _path


@pytest.fixture(name="mip_dna_store_files")
def fixture_mip_dna_store_files(apps_dir: Path) -> Path:
    """Return the path to the directory with mip dna store files"""
    _path = apps_dir / "mip" / "dna" / "store"
    return _path


@pytest.fixture(name="mip_deliverables_file")
def fixture_mip_deliverables_files(mip_dna_store_files: Path) -> Path:
    """Fixture for general deliverables file in mip"""
    return mip_dna_store_files / "case_id_deliverables.yaml"


# Orderform fixtures


@pytest.fixture
def microbial_orderform(orderforms: Path) -> str:
    """Orderform fixture for microbial samples"""
    _file = orderforms / "1603.9.microbial.xlsx"
    return str(_file)


@pytest.fixture
def rml_orderform():
    """Orderform fixture for RML samples"""
    return "tests/fixtures/orderforms/1604.9.rml.xlsx"


@pytest.fixture(name="madeline_output")
def fixture_madeline_output(apps_dir: Path) -> str:
    """File with madeline output"""
    _file = apps_dir / "madeline/madeline.xml"
    return str(_file)


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


@pytest.fixture(name="case_qc_metrics")
def fixture_case_qc_metrics(apps_dir: Path) -> Path:
    """Return the path to a qc metrics file with case data"""
    return Path("tests/fixtures/apps/mip/case_qc_metrics.yaml")


@pytest.fixture(name="bcf_file")
def fixture_bcf_file(apps_dir: Path) -> Path:
    """Return the path to a bcf file"""
    return apps_dir / "gt" / "yellowhog.bcf"


@pytest.fixture(scope="session", name="files")
def fixture_files():
    """Trailblazer api for mip files"""
    return {
        "config": "tests/fixtures/apps/mip/dna/store/case_config.yaml",
        "sampleinfo": "tests/fixtures/apps/mip/dna/store/case_qc_sample_info.yaml",
        "qcmetrics": "tests/fixtures/apps/mip/case_qc_metrics.yaml",
        "rna_config": "tests/fixtures/apps/mip/rna/case_config.yaml",
        "rna_sampleinfo": "tests/fixtures/apps/mip/rna/case_qc_sampleinfo.yaml",
        "rna_config_store": "tests/fixtures/apps/mip/rna/store/case_config.yaml",
        "rna_sampleinfo_store": "tests/fixtures/apps/mip/rna/store/case_qc_sample_info.yaml",
        "mip_rna_deliverables": "test/fixtures/apps/mip/rna/store/case_deliverables.yaml",
        "dna_config_store": "tests/fixtures/apps/mip/dna/store/case_config.yaml",
        "dna_sampleinfo_store": "tests/fixtures/apps/mip/dna/store/case_qc_sample_info.yaml",
        "mip_dna_deliverables": "test/fixtures/apps/mip/dna/store/case_deliverables.yaml",
    }


@pytest.fixture(scope="function", name="bed_file")
def fixture_bed_file(analysis_dir) -> str:
    """Get the path to a bed file file"""
    return str(analysis_dir / "sample_coverage.bed")


@pytest.fixture(scope="session", name="files_raw")
def fixture_files_raw(files):
    """Get some raw files"""
    return {
        "config": ruamel.yaml.safe_load(open(files["config"])),
        "sampleinfo": ruamel.yaml.safe_load(open(files["sampleinfo"])),
        "qcmetrics": ruamel.yaml.safe_load(open(files["qcmetrics"])),
        "rna_config": ruamel.yaml.safe_load(open(files["rna_config"])),
        "rna_sampleinfo": ruamel.yaml.safe_load(open(files["rna_sampleinfo"])),
        "rna_config_store": ruamel.yaml.safe_load(open(files["rna_config_store"])),
        "rna_sampleinfo_store": ruamel.yaml.safe_load(open(files["rna_sampleinfo_store"])),
        "dna_config_store": ruamel.yaml.safe_load(open(files["dna_config_store"])),
        "dna_sampleinfo_store": ruamel.yaml.safe_load(open(files["dna_sampleinfo_store"])),
    }


@pytest.fixture(scope="session")
def files_data(files_raw):
    """Get some data files"""
    return {
        "config": parse_sampleinfo.parse_config(files_raw["config"]),
        "sampleinfo": parse_sampleinfo.parse_sampleinfo(files_raw["sampleinfo"]),
        "qcmetrics": parse_qcmetrics.parse_qcmetrics(files_raw["qcmetrics"]),
        "rna_config": parse_sampleinfo.parse_config(files_raw["rna_config"]),
        "rna_sampleinfo": parse_sampleinfo.parse_sampleinfo_rna(files_raw["rna_sampleinfo"]),
        "rna_config_store": parse_sampleinfo.parse_config(files_raw["rna_config_store"]),
        "rna_sampleinfo_store": parse_sampleinfo.parse_sampleinfo(
            files_raw["rna_sampleinfo_store"]
        ),
        "dna_config_store": parse_sampleinfo.parse_config(files_raw["dna_config_store"]),
        "dna_sampleinfo_store": parse_sampleinfo.parse_sampleinfo(
            files_raw["dna_sampleinfo_store"]
        ),
    }


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
def fixture_timestamp_yesterday(timestamp_today) -> dt.datetime:
    """Return a time stamp of yesterdays date in date time format"""
    return timestamp_today - dt.timedelta(days=1)


@pytest.fixture(scope="function", name="hk_bundle_data")
def fixture_hk_bundle_data(case_id, bed_file, timestamp):
    """Get some bundle data for housekeeper"""
    data = {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [{"path": bed_file, "archive": False, "tags": ["bed", "sample"]}],
    }
    return data


@pytest.fixture(scope="function", name="sample_hk_bundle_no_files")
def fixture_sample_hk_bundle_no_files(sample, timestamp):
    """Create a complete bundle mock for testing compression"""
    hk_bundle_data = {
        "name": sample,
        "created": timestamp,
        "expires": timestamp,
        "files": [],
    }

    return hk_bundle_data


@pytest.fixture(scope="function", name="case_hk_bundle_no_files")
def fixture_case_hk_bundle_no_files(case_id, timestamp):
    """Create a complete bundle mock for testing compression"""
    hk_bundle_data = {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [],
    }

    return hk_bundle_data


@pytest.fixture(scope="function", name="compress_hk_fastq_bundle")
def fixture_compress_hk_fastq_bundle(compression_object, sample_hk_bundle_no_files):
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


@pytest.yield_fixture(scope="function", name="housekeeper_api")
def fixture_housekeeper_api(hk_config_dict):
    """Setup Housekeeper store."""
    _api = MockHousekeeperAPI(hk_config_dict)
    yield _api


@pytest.yield_fixture(scope="function", name="real_housekeeper_api")
def fixture_real_housekeeper_api(hk_config_dict):
    """Setup a real Housekeeper store."""
    _api = HousekeeperAPI(hk_config_dict)
    _api.initialise_db()
    yield _api


@pytest.yield_fixture(scope="function", name="populated_housekeeper_api")
def fixture_populated_housekeeper_api(housekeeper_api, hk_bundle_data, helpers):
    """Setup a Housekeeper store with some data."""
    hk_api = housekeeper_api
    helpers.ensure_hk_bundle(hk_api, hk_bundle_data)
    return hk_api


@pytest.yield_fixture(scope="function", name="hk_version_obj")
def fixture_hk_version_obj(housekeeper_api, hk_bundle_data, helpers):
    """Get a housekeeper version object"""
    _version = helpers.ensure_hk_version(housekeeper_api, hk_bundle_data)
    return _version


# Scout fixtures


@pytest.yield_fixture(scope="function", name="scout_api")
def fixture_scout_api():
    """Setup Scout api."""
    _api = MockScoutAPI()
    return _api


# Crunchy fixtures


@pytest.yield_fixture(scope="function", name="crunchy_api")
def fixture_crunchy_api():
    """Setup Crunchy api."""
    _api = MockCrunchyAPI()
    return _api


# Store fixtures


@pytest.yield_fixture(scope="function", name="analysis_store")
def fixture_analysis_store(
    base_store: Store, analysis_family: dict, wgs_application_tag: str, helpers
):
    """Setup a store instance for testing analysis API."""
    helpers.ensure_family_from_dict(
        base_store, family_info=analysis_family, app_tag=wgs_application_tag
    )

    yield base_store


@pytest.yield_fixture(scope="function", name="analysis_store_trio")
def fixture_analysis_store_trio(analysis_store):
    """Setup a store instance with a trion loaded for testing analysis API."""

    yield analysis_store


@pytest.yield_fixture(scope="function", name="analysis_store_single_case")
def fixture_analysis_store_single(base_store, analysis_family_single_case, helpers):
    """Setup a store instance with a single ind case for testing analysis API."""
    helpers.ensure_family_from_dict(base_store, family_info=analysis_family_single_case)

    yield base_store


@pytest.yield_fixture(scope="function", name="customer_group")
def fixture_customer_group() -> str:
    """Return a default customer group"""
    return "all_customers"


@pytest.yield_fixture(scope="function", name="customer_production")
def fixture_customer_production(customer_group) -> dict:
    """Return a dictionary with infomation about the prod customer"""
    _cust = dict(
        customer_id="cust000",
        name="Production",
        scout_access=True,
        customer_group=customer_group,
    )
    return _cust


@pytest.yield_fixture(scope="function", name="external_wgs_application_tag")
def fixture_external_wgs_application_tag() -> str:
    """Return the external wgs app tag"""
    return "WGXCUSC000"


@pytest.yield_fixture(scope="function", name="external_wgs_info")
def fixture_external_wgs_info(external_wgs_application_tag) -> dict:
    """Return a dictionary with information external WGS application"""
    _info = dict(
        application_tag=external_wgs_application_tag,
        application_type="wgs",
        description="External WGS",
        is_external=True,
        target_reads=10,
    )
    return _info


@pytest.yield_fixture(scope="function", name="external_wes_application_tag")
def fixture_external_wes_application_tag() -> str:
    """Return the external whole exome sequencing app tag"""
    return "EXXCUSR000"


@pytest.yield_fixture(scope="function", name="external_wes_info")
def fixture_external_wes_info(external_wes_application_tag) -> dict:
    """Return a dictionary with information external WES application"""
    _info = dict(
        application_tag=external_wes_application_tag,
        application_type="wes",
        description="External WES",
        is_external=True,
        target_reads=10,
    )
    return _info


@pytest.yield_fixture(scope="function", name="wgs_application_tag")
def fixture_wgs_application_tag() -> str:
    """Return the wgs app tag"""
    return "WGSPCFC060"


@pytest.yield_fixture(scope="function", name="wgs_application_info")
def fixture_wgs_application_info(wgs_application_tag) -> dict:
    """Return a dictionary with information the WGS application"""
    _info = dict(
        application_tag=wgs_application_tag,
        application_type="wgs",
        description="WGS, double",
        sequencing_depth=30,
        is_external=True,
        is_accredited=True,
        target_reads=10,
    )
    return _info


@pytest.yield_fixture(scope="function", name="store")
def fixture_store() -> Store:
    """Fixture with a CG store"""
    _store = Store(uri="sqlite:///")
    _store.create_all()
    yield _store
    _store.drop_all()


@pytest.yield_fixture(scope="function", name="base_store")
def fixture_base_store(store) -> Store:
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
            target_reads=10,
        ),
        store.add_application(
            tag="EXXCUSR000",
            category="wes",
            description="External WES",
            sequencing_depth=0,
            is_external=True,
            percent_kth=80,
            target_reads=10,
        ),
        store.add_application(
            tag="WGSPCFC060",
            category="wgs",
            description="WGS, double",
            sequencing_depth=30,
            accredited=True,
            percent_kth=80,
            target_reads=10,
        ),
        store.add_application(
            tag="RMLS05R150",
            category="rml",
            description="Ready-made",
            sequencing_depth=0,
            percent_kth=80,
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
        ),
        store.add_application(
            tag="METLIFR020",
            category="wgs",
            description="Whole genome metagenomics",
            sequencing_depth=0,
            target_reads=400000,
            percent_kth=80,
        ),
        store.add_application(
            tag="METNXTR020",
            category="wgs",
            description="Metagenomics",
            sequencing_depth=0,
            target_reads=200000,
            percent_kth=80,
        ),
        store.add_application(
            tag="MWRNXTR003",
            category="mic",
            description="Microbial whole genome ",
            sequencing_depth=0,
            percent_kth=80,
            target_reads=10,
        ),
        store.add_application(
            tag="RNAPOAR025",
            category="tgs",
            description="RNA seq, poly-A based priming",
            percent_kth=80,
            sequencing_depth=25,
            accredited=True,
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


@pytest.yield_fixture(scope="function")
def disk_store(cli_runner, invoke_cli) -> Store:
    """Store on disk"""
    database = "./test_db.sqlite3"
    database_path = Path(database)
    database_uri = f"sqlite:///{database}"
    with cli_runner.isolated_filesystem():
        assert database_path.exists() is False

        # WHEN calling "init"
        result = invoke_cli(["--database", database_uri, "init"])

        # THEN it should setup the database with some tables
        assert result.exit_code == 0
        assert database_path.exists()
        assert len(Store(database_uri).engine.table_names()) > 0

        yield Store(database_uri)


@pytest.fixture(scope="function", name="trailblazer_api")
def fixture_trailblazer_api() -> MockTB:
    return MockTB()
