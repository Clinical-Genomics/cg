from datetime import datetime, date
from pathlib import Path
from typing import List

import pytest
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.meta.upload.gisaid import GisaidAPI
from cg.meta.upload.gisaid.models import GisaidSample
from cg.models.cg_config import CGConfig, GisaidConfig, LimsConfig
from cg.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture(name="config_object_no_gisaid_samples")
def fixture_config_object_no_gisaid_samples(
    config: dict, cg_config_object: CGConfig, base_store: Store
):
    cg_config_object.status_db_ = base_store
    cg_config_object.gisaid = GisaidConfig(**config["gisaid"])
    return cg_config_object


@pytest.fixture(name="config_object")
def fixture_config_object(
    cg_context: CGConfig, analysis_store: Store, real_housekeeper_api: HousekeeperAPI
):
    cg_context.status_db_ = analysis_store
    cg_context.housekeeper_api_ = real_housekeeper_api
    return cg_context


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


@pytest.fixture(name="temp_result_file")
def fixture_temp_result_file() -> Path:
    file_path = Path("result_file_name")
    yield file_path
    try:
        file_path.unlink()
    except FileNotFoundError:
        pass


@pytest.fixture
def valid_gisiad_fasta_file() -> Path:
    """Get file path to valid fasta"""

    file_path = "tests/meta/upload/gisaid/fixtures/valid_gisaid.fasta"
    return Path(file_path)


@pytest.fixture
def valid_housekeeper_fasta_file() -> Path:
    """Get file path to valid fasta"""

    file_path = "tests/meta/upload/gisaid/fixtures/valid_housekeeper.fasta"
    return Path(file_path)


@pytest.fixture
def invalid_fasta_file() -> str:
    """Get file path to invalid fasta"""

    file_path = "tests/meta/upload/gisaid/fixtures/invalid_housekeeper.fasta"
    return Path(file_path)


@pytest.fixture
def gisaid_case_id():
    return "gisaid_case"


@pytest.fixture
def four_gisaid_samples(gisaid_case_id: str, temp_result_file: Path) -> List[GisaidSample]:
    return [
        GisaidSample(
            case_id=gisaid_case_id,
            cg_lims_id=f"s{i}",
            covv_subm_sample_id=f"s{i}",
            submitter="test_submitter",
            fn=temp_result_file.name,
            covv_collection_date="2020-11-22",
            region="Stockholm",
            region_code="01",
            covv_orig_lab="Karolinska University Hospital",
            covv_orig_lab_addr="171 76 Stockholm, Sweden",
        )
        for i in range(1, 5)
    ]


def get_sample_attribute(lims_id: str, key: str):
    udfs = {
        "original_lab_address": "171 76 Stockholm, Sweden",
        "original_lab": "Karolinska University Hospital",
        "region_code": "01",
        "collection_date": "2020-11-22",
        "region": "Stockholm",
    }
    return udfs[key]


@pytest.fixture
def dummy_gisaid_sample(temp_result_file: Path) -> GisaidSample:
    return GisaidSample(
        case_id="dummy_id",
        cg_lims_id=f"dummy_sample",
        covv_subm_sample_id="test_name",
        submitter="test_submitter",
        fn=temp_result_file.name,
        covv_collection_date="2020-11-22",
        region="Stockholm",
        region_code="01",
        covv_orig_lab="Karolinska University Hospital",
        covv_orig_lab_addr="171 76 Stockholm, Sweden",
    )


@pytest.fixture
def bundle_with_four_samples(gisaid_case_id, timestamp):
    file = Path("tests/meta/upload/gisaid/fixtures/valid.fasta")
    files = [{"path": str(file.absolute()), "archive": False, "tags": ["consensus"]}]
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
