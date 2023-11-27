"""Fixtures for observations."""


import pytest

from cg.apps.loqus import LoqusdbAPI
from cg.constants.observations import LOQUSDB_ID
from cg.constants.sequencing import SequencingMethod
from cg.meta.observations.balsamic_observations_api import BalsamicObservationsAPI
from cg.meta.observations.mip_dna_observations_api import MipDNAObservationsAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from tests.apps.loqus.conftest import (
    loqusdb_api,
    loqusdb_binary_path,
    loqusdb_config_dict,
    loqusdb_config_path,
    loqusdb_process,
    nr_of_loaded_variants,
)
from tests.cli.conftest import base_context
from tests.models.observations.conftest import (
    balsamic_observations_input_files,
    balsamic_observations_input_files_raw,
    observations_input_files,
    observations_input_files_raw,
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
    def get_case(*args, **kwargs) -> dict | None:
        """Mock get_case method."""
        _ = args
        _ = kwargs
        return {"case_id": "case_id", LOQUSDB_ID: "123"}

    @staticmethod
    def get_duplicate(*args, **kwargs) -> dict | None:
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
def mock_loqusdb_api(filled_file) -> MockLoqusdbAPI:
    """Mock Loqusdb API."""
    return MockLoqusdbAPI(binary_path=filled_file, config_path=filled_file)


@pytest.fixture(name="mip_dna_observations_api")
def mip_dna_observations_api(
    cg_config_object: CGConfig, mock_loqusdb_api: MockLoqusdbAPI, analysis_store: Store
) -> MipDNAObservationsAPI:
    """Rare diseases observations API fixture."""
    mip_dna_observations_api: MipDNAObservationsAPI = MipDNAObservationsAPI(
        config=cg_config_object, sequencing_method=SequencingMethod.WGS
    )
    mip_dna_observations_api.store = analysis_store
    mip_dna_observations_api.loqusdb_api = mock_loqusdb_api
    return mip_dna_observations_api


@pytest.fixture(name="balsamic_observations_api")
def balsamic_observations_api(
    cg_config_object: CGConfig, mock_loqusdb_api: MockLoqusdbAPI, analysis_store: Store
) -> BalsamicObservationsAPI:
    """Rare diseases observations API fixture."""
    balsamic_observations_api: BalsamicObservationsAPI = BalsamicObservationsAPI(
        config=cg_config_object, sequencing_method=SequencingMethod.WGS
    )
    balsamic_observations_api.store = analysis_store
    balsamic_observations_api.loqusdb_somatic_api = mock_loqusdb_api
    balsamic_observations_api.loqusdb_tumor_api = mock_loqusdb_api
    return balsamic_observations_api
