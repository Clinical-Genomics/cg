"""Fixtures for observations."""

import tempfile
from typing import Optional

import pytest

from cg.models.observations.input_files import MipDNAObservationsInputFiles
from cg.store import models

from cg.apps.loqus import LoqusdbAPI
from cg.constants.sequencing import SequencingMethod
from cg.meta.upload.observations.mip_dna_observations_api import MipDNAObservationsAPI
from cg.models.cg_config import CGConfig

from tests.apps.loqus.conftest import (
    fixture_loqusdb_config_dict,
    fixture_loqusdb_binary_path,
    fixture_loqusdb_config_path,
    fixture_loqusdb_api,
    fixture_loqusdb_process,
    fixture_loqusdb_case_output,
)
from tests.models.observations.conftest import (
    fixture_observations_input_files,
    fixture_observations_input_files_dict,
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
        return {"case_id": "case_id", "_id": "123"}

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


class MockMipDNAObservationsAPI(MipDNAObservationsAPI):
    """Mock MipDNAObservationsAPI class."""

    def get_loqusdb_api(self, case: models.Family) -> LoqusdbAPI:
        """Mock get_loqusdb_api method."""
        return MockLoqusdbAPI(binary_path="binary", config_path="config")

    def get_observations_input_files(self, case: models.Family) -> MipDNAObservationsInputFiles:
        """Mock get_observations_input_files method."""
        return MipDNAObservationsInputFiles(
            snv_vcf_path=tempfile.gettempdir(), family_ped_path=tempfile.gettempdir()
        )

    def is_duplicate(
        self,
        case: models.Family,
        loqusdb_api: LoqusdbAPI,
        input_files: MipDNAObservationsInputFiles,
    ) -> bool:
        """Mock is_duplicate method."""
        return False


class MockMipDNAObservationsAPIDuplicateCase(MockMipDNAObservationsAPI):
    """Mock MipDNAObservationsAPI class with a duplicate case."""

    def is_duplicate(
        self,
        case: models.Family,
        loqusdb_api: LoqusdbAPI,
        input_files: MipDNAObservationsInputFiles,
    ) -> bool:
        """Mock is_duplicate method."""
        return True


@pytest.fixture(scope="function", name="mock_loqusdb_api")
def fixture_mock_loqusdb_api() -> MockLoqusdbAPI:
    """Mock Loqusdb API."""
    return MockLoqusdbAPI(binary_path="binary", config_path="config")


@pytest.fixture(scope="function", name="mock_mip_dna_observations_api")
def fixture_mock_mip_dna_observations_api(cg_config_object: CGConfig) -> MockMipDNAObservationsAPI:
    """Mocked observations API."""
    return MockMipDNAObservationsAPI(cg_config_object, SequencingMethod.WGS)


@pytest.fixture(scope="function", name="mock_mip_dna_observations_api_duplicate_case")
def fixture_mock_mip_dna_observations_api_duplicate_case(
    cg_config_object: CGConfig,
) -> MockMipDNAObservationsAPI:
    """Mocked observations API with a duplicate case."""
    return MockMipDNAObservationsAPIDuplicateCase(cg_config_object, SequencingMethod.WGS)


@pytest.fixture(scope="function", name="mip_dna_observations_api")
def fixture_mip_dna_observations_api(cg_config_object: CGConfig) -> MipDNAObservationsAPI:
    """Rare diseases observations API fixture."""
    return MipDNAObservationsAPI(cg_config_object, SequencingMethod.WGS)
