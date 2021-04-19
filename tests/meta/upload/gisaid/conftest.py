from pathlib import Path
from typing import List

from cg.apps.housekeeper.hk import HousekeeperAPI
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


@pytest.fixture(name="config_object_no_gisaid_samples")
def fixture_config_object_no_gisaid_samples(
    config: dict, cg_config_object: CGConfig, base_store: Store
):
    cg_config_object.status_db_ = base_store
    cg_config_object.gisaid = GisaidConfig(**config["gisaid"])
    return cg_config_object


@pytest.fixture(name="config_object")
def fixture_config_object(config: dict, cg_config_object: CGConfig, analysis_store: Store):
    cg_config_object.status_db_ = analysis_store
    cg_config_object.gisaid = GisaidConfig(**config["gisaid"])
    return cg_config_object


@pytest.fixture(scope="function")
def gisaid_api(config_object):
    """
    gisaid API fixture
    """
    return GisaidAPI(config=config_object)


@pytest.fixture(scope="function")
def gisaid_api_no_samples(config_object_no_gisaid_samples):
    """
    gisaid API fixture
    """
    return GisaidAPI(config=config_object_no_gisaid_samples)


@pytest.fixture
def valid_concat_fasta_file() -> str:
    """Get file path to valid fasta"""

    file_path = "tests/meta/upload/gisaid/fixtures/concat.fasta"
    file = Path(file_path)
    return file.read_text()


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
def gisaid_case_id():
    return "gisaid_case"


@pytest.fixture
def four_gisaid_samples(gisaid_case_id) -> List[GisaidSample]:

    return [
        GisaidSample(
            family_id=gisaid_case_id,
            cg_lims_id=f"s{i}",
            covv_subm_sample_id="test_name",
            submitter="test_submitter",
            fn=f"test.fasta",
            covv_collection_date="2020-11-22",
            lab="Stockholm",
        )
        for i in range(1, 5)
    ]


@pytest.fixture
def dummy_gisaid_sample() -> GisaidSample:

    return GisaidSample(
        family_id="dummy_id",
        cg_lims_id=f"dummy_sample",
        covv_subm_sample_id="test_name",
        submitter="test_submitter",
        fn=f"test.fasta",
        covv_collection_date="2020-11-22",
        lab="Stockholm",
    )


@pytest.fixture
def bundle_with_four_samples(gisaid_case_id, timestamp):
    files = []
    for i in range(1, 5):
        file = Path(f"tests/meta/upload/gisaid/fixtures/s{i}_valid.fasta")
        files.append(
            {"path": str(file.absolute()), "archive": False, "tags": ["consensus", f"s{i}"]}
        )

    return {
        "name": gisaid_case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": files,
    }


@pytest.fixture
def four_samples_csv() -> str:
    file_path = "tests/meta/upload/gisaid/fixtures/four_samples.csv"
    file = Path(file_path)
    return file.read_text()
