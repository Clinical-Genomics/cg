"""Loqusdb API fixtures."""

import pytest
from pytest_mock import MockFixture

from cg.apps.lims import LimsAPI
from cg.apps.loqus import LoqusdbAPI
from cg.constants.observations import LOQUSDB_ID
from cg.constants.sample_sources import SourceType
from cg.meta.observations.balsamic_observations_api import BalsamicObservationsAPI
from cg.meta.observations.mip_dna_observations_api import MipDNAObservationsAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case, Customer
from cg.store.store import Store


@pytest.fixture
def balsamic_observations_api(
    cg_context: CGConfig,
    analysis_store: Store,
    lims_api: LimsAPI,
    loqusdb_api: LoqusdbAPI,
    case_id: str,
    balsamic_customer: Customer,
    number_of_loaded_variants: int,
    loqusdb_id: str,
    mocker: MockFixture,
) -> BalsamicObservationsAPI:
    """Cancer observations API fixture."""
    balsamic_observations_api: BalsamicObservationsAPI = BalsamicObservationsAPI(cg_context)
    balsamic_observations_api.store = analysis_store
    balsamic_observations_api.loqusdb_somatic_api = loqusdb_api
    balsamic_observations_api.loqusdb_tumor_api = loqusdb_api

    # Mocked case scenario for Balsamic uploads
    case: Case = analysis_store.get_case_by_internal_id(case_id)
    case.customer.internal_id = balsamic_customer.internal_id
    case.samples[0].is_tumour = True

    # Mocked Loqusdb API scenario for Balsamic uploads
    mocker.patch.object(LoqusdbAPI, "load", return_value={"variants": number_of_loaded_variants})
    mocker.patch.object(
        LoqusdbAPI, "get_case", return_value={"case_id": case_id, LOQUSDB_ID: loqusdb_id}
    )

    # Mocked LIMS API scenario
    mocker.patch.object(LimsAPI, "get_source", return_value=SourceType.TISSUE)

    return balsamic_observations_api


@pytest.fixture
def mip_dna_observations_api(
    cg_context: CGConfig,
    analysis_store: Store,
    lims_api: LimsAPI,
    loqusdb_api: LoqusdbAPI,
    case_id: str,
    mip_dna_customer: Customer,
    number_of_loaded_variants: int,
    loqusdb_id: str,
    mocker: MockFixture,
) -> MipDNAObservationsAPI:
    """Rare diseases observations API fixture."""
    mip_dna_observations_api: MipDNAObservationsAPI = MipDNAObservationsAPI(cg_context)
    mip_dna_observations_api.store = analysis_store
    mip_dna_observations_api.loqusdb_api = loqusdb_api

    # Mocked case scenario for MIP-DNA uploads
    case: Case = analysis_store.get_case_by_internal_id(case_id)
    case.customer.internal_id = mip_dna_customer.internal_id

    # Mocked Loqusdb API scenario for MIP-DNA uploads
    mocker.patch.object(LoqusdbAPI, "load", return_value={"variants": number_of_loaded_variants})
    mocker.patch.object(
        LoqusdbAPI, "get_case", return_value={"case_id": case_id, LOQUSDB_ID: loqusdb_id}
    )

    # Mocked LIMS API scenario
    mocker.patch.object(LimsAPI, "get_source", return_value=SourceType.TISSUE)

    return mip_dna_observations_api
