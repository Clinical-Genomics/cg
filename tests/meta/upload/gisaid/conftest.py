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


@pytest.fixture(name="temp_result_file")
def fixture_temp_result_file() -> Path:
    file_path = Path("result_file_name")
    yield file_path
    try:
        file_path.unlink()
    except FileNotFoundError:
        pass


@pytest.fixture
def gisaid_case_id():
    return "gisaid_case"


def get_sample_attribute(lims_id: str, key: str):
    udfs = {
        "original_lab_address": "171 76 Stockholm, Sweden",
        "original_lab": "Karolinska University Hospital",
        "region_code": "01",
        "collection_date": "2020-11-22",
        "region": "Stockholm",
    }
    return udfs[key]
