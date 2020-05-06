"""
    Conftest file for pytest fixtures
"""
import datetime as dt
from pathlib import Path

import pytest
import ruamel.yaml
from trailblazer.mip import files as mip_dna_files_api

from cg.apps.mip_rna import files as mip_rna_files_api
from cg.meta.store import mip_rna as store_mip_rna
from cg.store import Store

from .mocks.hk_mock import MockHK, MockVersion
from .mocks.madeline import MockMadelineAPI

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

# Case fixtures


@pytest.fixture(name="case_id")
def fixture_case_id():
    """Return a case id"""
    return "yellowhog"


@pytest.fixture(name="family_info")
def fixture_family_info(case_id):
    """Get family information in a dictionary."""
    family = {
        "name": "family",
        "internal_id": case_id,
        "panels": ["IEM", "EP"],
        "samples": [
            {
                "name": "son",
                "sex": "male",
                "internal_id": "ADM1",
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
                "status": "unaffected",
                "ticket_number": 123456,
                "reads": 6000000,
            },
            {
                "name": "mother",
                "sex": "female",
                "internal_id": "ADM3",
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


# Object fixtures


@pytest.yield_fixture(scope="function", name="hk_version_obj")
def fixture_hk_version_obj():
    """class fixtures are not supported, so make a function out of a class"""
    return MockVersion()


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
def fixture_madeline_output(fixtures_dir: Path) -> str:
    """File with madeline output"""
    _file = fixtures_dir / "apps/madeline/madeline.xml"
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


@pytest.fixture(scope="function")
def tmp_file(tmp_path):
    """Get a temp file"""
    return tmp_path / "test"


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
        "rna_sampleinfo": mip_rna_files_api.parse_sampleinfo_rna(
            files_raw["rna_sampleinfo"]
        ),
    }


@pytest.yield_fixture(scope="function", name="store")
def fixture_store() -> Store:
    """Fixture with a CG store"""
    _store = Store(uri="sqlite://")
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
        ),
        store.add_application(
            tag="EXXCUSR000",
            category="wes",
            description="External WES",
            sequencing_depth=0,
            is_external=True,
            percent_kth=80,
        ),
        store.add_application(
            tag="WGSPCFC060",
            category="wgs",
            description="WGS, double",
            sequencing_depth=30,
            accredited=True,
            percent_kth=80,
        ),
        store.add_application(
            tag="RMLS05R150",
            category="rml",
            description="Ready-made",
            sequencing_depth=0,
            percent_kth=80,
        ),
        store.add_application(
            tag="WGTPCFC030",
            category="wgs",
            description="WGS trio",
            is_accredited=True,
            sequencing_depth=30,
            target_reads=300000000,
            limitations="some",
            percent_kth=80,
        ),
        store.add_application(
            tag="METLIFR020",
            category="wgs",
            description="Whole genome metagenomics",
            sequencing_depth=0,
            target_reads=40000000,
            percent_kth=80,
        ),
        store.add_application(
            tag="METNXTR020",
            category="wgs",
            description="Metagenomics",
            sequencing_depth=0,
            target_reads=20000000,
            percent_kth=80,
        ),
        store.add_application(
            tag="MWRNXTR003",
            category="mic",
            description="Microbial whole genome ",
            sequencing_depth=0,
            percent_kth=80,
        ),
        store.add_application(
            tag="RNAPOAR025",
            category="tgs",
            description="RNA seq, poly-A based priming",
            percent_kth=80,
            sequencing_depth=25,
            accredited=True,
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
        sample.application_version = (
            external_app if "external" in sample.name else wgs_app
        )
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
