from pathlib import Path
from typing import List

from cg.meta.upload.gisaid.models import GisaidSample
from cg.models.cg_config import CGConfig, GisaidConfig
import pytest

from cg.meta.upload.gisaid import GisaidAPI
from cg.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture(name="config")
def fixture_config(root_path) -> dict:
    """Return a dictionary with housekeeper api configs for testing"""
    return {"gisaid": {"binary_path": "/path/to/gisaid", "submitter": "some submitter"}}


@pytest.fixture(name="gisaid_store")
def fixture_gisaid_store(analysis_store: Store, helpers: StoreHelpers):
    app_tag = "ABC123"
    family = helpers.add_case(store=analysis_store, internal_id="gisaid_family_id")
    helpers.add_application(
        store=analysis_store,
        target_reads=1000000,
        application_tag=app_tag,
    )

    helpers.ensure_application_version(store=analysis_store, application_tag=app_tag)

    common_sample_data = dict(
        store=analysis_store,
        sequencing_qc=True,
        reads=100000000,
        application_tag=app_tag,
    )

    for i in range(5):
        sample = helpers.add_sample(**common_sample_data, internal_id=f"id{i}", name=f"name{i}")
        helpers.add_relationship(store=analysis_store, sample=sample, case=family)

    return analysis_store


@pytest.fixture(name="config_object")
def fixture_config_object(config: dict, cg_config_object: CGConfig, gisaid_store: Store):
    cg_config_object.status_db_ = gisaid_store
    cg_config_object.gisaid = GisaidConfig(**config["gisaid"])
    return cg_config_object


@pytest.fixture(scope="function")
def gisaid_api(config_object):
    """
    gisaid API fixture
    """
    return GisaidAPI(config=config_object)


@pytest.fixture(name="config_object_no_gisaid_samples")
def fixture_config_object_no_gisaid_samples(
    config: dict, cg_config_object: CGConfig, base_store: Store
):
    cg_config_object.status_db_ = base_store
    cg_config_object.gisaid = GisaidConfig(**config["gisaid"])
    return cg_config_object


@pytest.fixture(scope="function")
def gisaid_api_no_samples(config_object_no_gisaid_samples):
    """
    gisaid API fixture
    """
    return GisaidAPI(config=config_object_no_gisaid_samples)


@pytest.fixture
def valid_fasta_file() -> str:
    """Get file path to valid fasta"""

    file_path = "tests/meta/upload/gisaid/fixtures/valid.fasta"
    file = Path(file_path)
    return str(file.absolute())


@pytest.fixture
def invalid_fasta_file() -> str:
    """Get file path to invalid fasta"""

    file_path = "tests/meta/upload/gisaid/fixtures/invalid.fasta"
    file = Path(file_path)
    return str(file.absolute())


@pytest.fixture
def four_gisaid_samples() -> List[GisaidSample]:
    samples = []
    while len(samples) < 3:
        samples.append(
            GisaidSample(
                family_id="family_id",
                cg_lims_id="some_id",
                covv_subm_sample_id="test_name",
                submitter="test_submitter",
                fn=f"test.fasta",
                covv_collection_date="2020-11-22",
                lab="Stockholm",
            )
        )
    return samples


@pytest.fixture
def four_samples_csv() -> str:
    file_path = "tests/meta/upload/gisaid/fixtures/four_samples.csv"
    file = Path(file_path)
    return file.read_text()
