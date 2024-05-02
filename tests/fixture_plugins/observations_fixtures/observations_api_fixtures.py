"""Loqusdb API fixtures."""

import pytest

from cg.apps.lims import LimsAPI
from cg.meta.observations.balsamic_observations_api import BalsamicObservationsAPI
from cg.meta.observations.mip_dna_observations_api import MipDNAObservationsAPI
from cg.models.cg_config import CGConfig
from cg.store.store import Store


@pytest.fixture
def balsamic_observations_api(
    cg_context: CGConfig, analysis_store: Store, lims_api: LimsAPI
) -> BalsamicObservationsAPI:
    """Cancer observations API fixture."""
    balsamic_observations_api: BalsamicObservationsAPI = BalsamicObservationsAPI(cg_context)
    balsamic_observations_api.store = analysis_store
    balsamic_observations_api.lims_api = lims_api
    return balsamic_observations_api


@pytest.fixture
def mip_dna_observations_api(
    cg_context: CGConfig, analysis_store: Store, lims_api: LimsAPI
) -> MipDNAObservationsAPI:
    """Rare diseases observations API fixture."""
    mip_dna_observations_api: MipDNAObservationsAPI = MipDNAObservationsAPI(cg_context)
    mip_dna_observations_api.store = analysis_store
    mip_dna_observations_api.analysis_api.lims_api = lims_api
    return mip_dna_observations_api
