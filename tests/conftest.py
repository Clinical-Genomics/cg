"""
    Conftest file for pytest fixtures
"""
import datetime as dt
import logging
import shutil
from pathlib import Path

import pytest
import ruamel.yaml
from trailblazer.mip import files as mip_dna_files_api

# from cg.apps.hk import HousekeeperAPI
from cg.apps.mip_rna import files as mip_rna_files_api
from cg.meta.store import mip_rna as store_mip_rna
from cg.store import Store

from .mocks.hk_mock import MockHousekeeperAPI
from .mocks.madeline import MockMadelineAPI
from .store_helpers import Helpers

CHANJO_CONFIG = {"chanjo": {"config_path": "chanjo_config", "binary_path": "chanjo"}}
CRUNCHY_CONFIG = {
    "crunchy": {
        "cram_reference": "/path/to/fasta",
        "slurm": {
            "account": "mock_account",
            "mail_user": "mock_mail",
            "conda_env": "mock_env",
        },
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


@pytest.yield_fixture(scope="function", name="analysis_family")
def fixture_analysis_family(case_id, family_name) -> dict:
    """Return a dictionary with information from a analysis family"""
    family = {
        "name": family_name,
        "internal_id": case_id,
        "panels": ["IEM", "EP"],
        "samples": [
            {
                "name": "son",
                "sex": "male",
                "internal_id": "ADM1",
                "data_analysis": "mip",
                "father": "ADM2",
                "mother": "ADM3",
                "status": "affected",
                "ticket_number": 123456,
                "reads": 5000000,
            },
            {
                "name": "father",
                "sex": "male",
                "internal_id": "ADM2",
                "data_analysis": "mip",
                "status": "unaffected",
                "ticket_number": 123456,
                "reads": 6000000,
            },
            {
                "name": "mother",
                "sex": "female",
                "internal_id": "ADM3",
                "data_analysis": "mip",
                "status": "unaffected",
                "ticket_number": 123456,
                "reads": 7000000,
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


# Api fixtures


@pytest.yield_fixture(scope="function")
def madeline_api(madeline_output):
    """madeline_api fixture"""
    _api = MockMadelineAPI()
    _api._madeline_outpath = madeline_output

    yield _api


@pytest.fixture
def balsamic_orderform():
    """Orderform fixture for Balsamic samples"""
    return "tests/fixtures/orderforms/1508.20.balsamic.xlsx"


@pytest.fixture
def external_orderform():
    """Orderform fixture for external samples"""
    return "tests/fixtures/orderforms/1541.6.external.xlsx"


@pytest.fixture
def fastq_orderform():
    """Orderform fixture for fastq samples"""
    return "tests/fixtures/orderforms/1508.20.fastq.xlsx"


# Files fixtures


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


@pytest.fixture(name="orderforms")
def fixture_orderform(fixtures_dir: Path) -> Path:
    """Return the path to the directory with orderforms"""
    _path = fixtures_dir / "orderforms"
    return _path


@pytest.fixture
def microbial_orderform(orderforms: Path) -> str:
    """Orderform fixture for microbial samples"""
    _file = orderforms / "1603.9.microbial.xlsx"
    return str(_file)


@pytest.fixture
def mip_orderform():
    """Orderform fixture for MIP samples"""
    return "tests/fixtures/orderforms/1508.20.mip.xlsx"


@pytest.fixture
def mip_balsamic_orderform():
    """Orderform fixture for MIP and Balsamic samples"""
    return "tests/fixtures/orderforms/1508.20.mip_balsamic.xlsx"


@pytest.fixture
def mip_rna_orderform():
    """Orderform fixture for MIP RNA samples"""
    return "tests/fixtures/orderforms/1508.20.mip_rna.xlsx"


@pytest.fixture
def rml_orderform():
    """Orderform fixture for RML samples"""
    return "tests/fixtures/orderforms/1604.9.rml.xlsx"


@pytest.fixture(name="madeline_output")
def fixture_madeline_output(apps_dir: Path) -> str:
    """File with madeline output"""
    _file = apps_dir / "madeline/madeline.xml"
    return str(_file)


@pytest.fixture(scope="session", name="files")
def fixture_files():
    """Trailblazer api for mip files"""
    return {
        "config": "tests/fixtures/apps/tb/case/case_config.yaml",
        "sampleinfo": "tests/fixtures/apps/tb/case/case_qc_sample_info.yaml",
        "qcmetrics": "tests/fixtures/apps/tb/case/case_qc_metrics.yaml",
        "rna_config": "tests/fixtures/apps/mip/rna/case_config.yaml",
        "rna_sampleinfo": "tests/fixtures/apps/mip/rna/case_qc_sampleinfo.yaml",
        "rna_config_store": "tests/fixtures/apps/mip/rna/store/case_config.yaml",
        "rna_sampleinfo_store": "tests/fixtures/apps/mip/rna/store/case_qc_sample_info.yaml",
        "mip_rna_deliverables": "test/fixtures/apps/mip/rna/store/case_deliverables.yaml",
    }


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
        "rna_sampleinfo_store": ruamel.yaml.safe_load(
            open(files["rna_sampleinfo_store"])
        ),
    }


@pytest.fixture(scope="session")
def files_data(files_raw):
    """Get some data files"""
    return {
        "config": mip_dna_files_api.parse_config(files_raw["config"]),
        "sampleinfo": mip_dna_files_api.parse_sampleinfo(files_raw["sampleinfo"]),
        "qcmetrics": mip_dna_files_api.parse_qcmetrics(files_raw["qcmetrics"]),
        "rna_config": mip_dna_files_api.parse_config(files_raw["rna_config"]),
        "rna_sampleinfo": mip_rna_files_api.parse_sampleinfo_rna(
            files_raw["rna_sampleinfo"]
        ),
        "rna_config_store": store_mip_rna.parse_config(files_raw["rna_config_store"]),
        "rna_sampleinfo_store": store_mip_rna.parse_sampleinfo(
            files_raw["rna_sampleinfo_store"]
        ),
    }


# Helper fixtures


@pytest.fixture(name="helpers")
def fixture_helpers():
    """Return a class with helper functions"""
    return Helpers()


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


@pytest.yield_fixture(scope="function", name="housekeeper_api")
def fixture_housekeeper_api(root_path):
    """Setup Housekeeper store."""
    _api = MockHousekeeperAPI(
        {"housekeeper": {"database": "sqlite:///:memory:", "root": str(root_path)}}
    )
    return _api


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


# Store fixtures


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
def fixture_base_store(
    store,
    customer_production,
    external_wgs_info,
    wgs_application_info,
    external_wes_info,
    helpers,
) -> Store:
    """Populate a store with customers, applications, versions and a bed."""
    customer_group = "all_customers"
    LOG.info("Adding customer %s", "cust000")
    helpers.ensure_customer(store, **customer_production)
    LOG.info("Adding customer %s", "cust001")
    helpers.ensure_customer(
        store, customer_id="cust001", name="Customer", customer_group=customer_group,
    )
    LOG.info("Adding customer %s", "cust002")
    helpers.ensure_customer(
        store,
        customer_id="cust002",
        name="Klinisk Genetik",
        scout_access=True,
        customer_group=customer_group,
    )
    LOG.info("Adding customer %s", "cust003")
    helpers.ensure_customer(
        store,
        customer_id="cust003",
        name="CMMS",
        scout_access=True,
        customer_group=customer_group,
    )

    LOG.info("Adding application %s", "External WGS")
    app_tags = []
    application = helpers.add_application(store, **external_wgs_info)
    app_tags.append(application.tag)

    LOG.info("Adding application %s", "External WES")
    application = helpers.add_application(store, **external_wes_info)
    app_tags.append(application.tag)

    LOG.info("Adding application %s", "WGS, double")
    application = helpers.add_application(store, **wgs_application_info)
    app_tags.append(application.tag)

    LOG.info("Adding application %s", "Ready-made")
    application = helpers.add_application(
        store,
        application_tag="RMLS05R150",
        application_type="rml",
        description="Ready-made",
    )
    app_tags.append(application.tag)

    LOG.info("Adding application %s", "WGS trio")
    application = helpers.add_application(
        store,
        application_tag="WGTPCFC030",
        application_type="wgs",
        description="WGS trio",
        is_accredited=True,
        target_reads=300000000,
        limitations="some",
    )
    app_tags.append(application.tag)

    LOG.info("Adding application %s", "Whole genome metagenomics")
    application = helpers.add_application(
        store,
        application_tag="METLIFR020",
        application_type="wgs",
        description="Whole genome metagenomics",
        sequencing_depth=0,
        target_reads=40000000,
    )
    app_tags.append(application.tag)

    LOG.info("Adding application %s", "Metagenomics")
    application = helpers.add_application(
        store,
        application_tag="METNXTR020",
        application_type="wgs",
        description="Metagenomics",
        sequencing_depth=0,
        target_reads=20000000,
    )
    app_tags.append(application.tag)

    LOG.info("Adding application %s", "Microbial whole genome")
    application = helpers.add_application(
        store,
        application_tag="MWRNXTR003",
        application_type="mic",
        description="Microbial whole genome",
        sequencing_depth=0,
    )
    app_tags.append(application.tag)

    LOG.info("Adding application %s", "RNA seq, poly-A based priming")
    application = helpers.add_application(
        store,
        application_tag="RNAPOAR025",
        application_type="tgs",
        description="RNA seq, poly-A based priming",
        sequencing_depth=25,
        is_accredited=True,
    )
    app_tags.append(application.tag)

    for app_tag in app_tags:
        helpers.ensure_application_version(store, app_tag)

    helpers.ensure_bed_version(store, bed_name="Bed")
    helpers.add_organism(store, internal_id="C. jejuni", name="C. jejuni")

    yield store


@pytest.fixture(scope="function")
def sample_store(
    store, customer_production, external_wgs_info, wgs_application_info, helpers
) -> Store:
    """Get a populated store with samples."""
    helpers.ensure_customer(store, **customer_production)
    helpers.ensure_application_version(store, **external_wgs_info)
    external_tag = external_wgs_info["application_tag"]
    helpers.ensure_application_version(store, **wgs_application_info)
    wgs_tag = wgs_application_info["application_tag"]
    helpers.add_sample(
        store, sample_id="ordered", gender="male", application_tag=wgs_tag
    )
    helpers.add_sample(
        store,
        sample_id="received",
        gender="unknown",
        application_tag=wgs_tag,
        received_at=dt.datetime.now(),
    )

    helpers.add_sample(
        store,
        sample_id="received-prepared",
        gender="unknown",
        application_tag=wgs_tag,
        received_at=dt.datetime.now(),
        prepared_at=dt.datetime.now(),
    )

    helpers.add_sample(
        store,
        sample_id="received-prepared",
        gender="unknown",
        application_tag=wgs_tag,
        received_at=dt.datetime.now(),
        prepared_at=dt.datetime.now(),
    )

    helpers.add_sample(
        store,
        sample_id="external",
        gender="female",
        application_tag=external_tag,
        external=True,
    )

    helpers.add_sample(
        store,
        sample_id="external-received",
        gender="female",
        is_external=True,
        application_tag=external_tag,
        received_at=dt.datetime.now(),
    )

    helpers.add_sample(
        store,
        sample_id="sequenced",
        gender="male",
        received_at=dt.datetime.now(),
        prepared_at=dt.datetime.now(),
        sequenced_at=dt.datetime.now(),
        reads=(310 * 1000000),
    )

    helpers.add_sample(
        store,
        sample_id="sequenced-partly",
        gender="male",
        received_at=dt.datetime.now(),
        prepared_at=dt.datetime.now(),
        reads=(250 * 1000000),
    )
    return store


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
