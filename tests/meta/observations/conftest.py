"""Fixtures for observations."""

from typing import Optional

import pytest

from cg.apps.loqus import LoqusdbAPI
from cg.constants.observations import LOQUSDB_ID
from cg.constants.sequencing import SequencingMethod
from cg.meta.observations.balsamic_observations_api import BalsamicObservationsAPI
from cg.meta.observations.mip_dna_observations_api import MipDNAObservationsAPI
from cg.models.cg_config import CGConfig

from tests.cli.conftest import fixture_base_context
from tests.apps.loqus.conftest import (
    fixture_loqusdb_config,
    fixture_nr_of_loaded_variants,
    fixture_loqusdb_binary_path,
    fixture_loqusdb_config_path,
    fixture_loqusdb_process,
    fixture_loqusdb_api,
)
from tests.models.observations.conftest import (
    fixture_observations_input_files_raw,
    fixture_observations_input_files,
    fixture_balsamic_observations_input_files_raw,
    fixture_balsamic_observations_input_files,
)


class MockLoqusdbAPI(LoqusdbAPI):
    """Mock LoqusdbAPI class."""

    def __init__(self, binary_path: str, config_path: str):
        super().__init__(binary_path, config_path)

    @staticmethod
    def load(*args, **kwargs) -> dict:
        """Mock load method."""
        _ = args
        _ = kwargs
        return dict(variants=15)

    @staticmethod
    def get_case(*args, **kwargs) -> Optional[dict]:
        """Mock get_case method."""
        _ = args
        _ = kwargs
        return {"case_id": "case_id", LOQUSDB_ID: "123"}

    @staticmethod
    def get_duplicate(*args, **kwargs) -> Optional[dict]:
        """Mock get_duplicate method."""
        _ = args
        _ = kwargs
        return {"case_id": "case_id"}

    @staticmethod
    def delete_case(*args, **kwargs) -> None:
        """Mock delete_case method."""
        _ = args
        _ = kwargs
        return None


@pytest.fixture(name="mock_loqusdb_api")
def fixture_mock_loqusdb_api(filled_file) -> MockLoqusdbAPI:
    """Mock Loqusdb API."""
    return MockLoqusdbAPI(binary_path=filled_file, config_path=filled_file)


@pytest.fixture(name="mip_dna_observations_api")
def fixture_mip_dna_observations_api(
    cg_config_object: CGConfig, mock_loqusdb_api: MockLoqusdbAPI
) -> MipDNAObservationsAPI:
    """Rare diseases observations API fixture."""
    mip_dna_observations_api = MipDNAObservationsAPI(cg_config_object, SequencingMethod.WGS)
    mip_dna_observations_api.loqusdb_api = mock_loqusdb_api
    return mip_dna_observations_api


@pytest.fixture(name="balsamic_observations_api")
def fixture_balsamic_observations_api(
    cg_config_object: CGConfig, mock_loqusdb_api: MockLoqusdbAPI
) -> BalsamicObservationsAPI:
    """Rare diseases observations API fixture."""
    balsamic_observations_api = BalsamicObservationsAPI(cg_config_object, SequencingMethod.WGS)
    balsamic_observations_api.loqusdb_somatic_api = mock_loqusdb_api
    balsamic_observations_api.loqusdb_tumor_api = mock_loqusdb_api
    return balsamic_observations_api
