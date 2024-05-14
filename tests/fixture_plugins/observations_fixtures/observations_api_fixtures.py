"""Loqusdb API fixtures."""

import pytest

from cg.apps.lims import LimsAPI
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
    case_id: str,
    balsamic_customer: Customer,
) -> BalsamicObservationsAPI:
    """Cancer observations API fixture."""
    balsamic_observations_api: BalsamicObservationsAPI = BalsamicObservationsAPI(cg_context)
    balsamic_observations_api.store = analysis_store
    case: Case = analysis_store.get_case_by_internal_id(case_id)
    case.customer.internal_id = balsamic_customer.internal_id
    case.samples[0].is_tumour = True
    return balsamic_observations_api


@pytest.fixture
def mip_dna_observations_api(
    cg_context: CGConfig,
    analysis_store: Store,
    lims_api: LimsAPI,
    case_id: str,
    mip_dna_customer: Customer,
) -> MipDNAObservationsAPI:
    """Rare diseases observations API fixture."""
    mip_dna_observations_api: MipDNAObservationsAPI = MipDNAObservationsAPI(cg_context)
    mip_dna_observations_api.store = analysis_store
    case: Case = analysis_store.get_case_by_internal_id(case_id)
    case.customer.internal_id = mip_dna_customer.internal_id
    return mip_dna_observations_api
