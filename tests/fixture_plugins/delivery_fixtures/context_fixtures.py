"""Delivery API context fixtures."""

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import DataDelivery, Workflow
from cg.models.cg_config import CGConfig
from cg.store.models import Case, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture
def delivery_housekeeper_api(real_housekeeper_api: HousekeeperAPI, helpers: StoreHelpers):
    """Delivery API Housekeeper context."""
    # TODO
    helpers.ensure_hk_bundle(real_housekeeper_api, "")
    helpers.ensure_hk_bundle(real_housekeeper_api, "")
    return real_housekeeper_api


@pytest.fixture
def delivery_context(
    cg_context: CGConfig,
    delivery_housekeeper_api: HousekeeperAPI,
    helpers: StoreHelpers,
    case_id: str,
    another_case_id: str,
    no_sample_case_id: str,
    case_name: str,
    another_case_name: str,
    sample_id: str,
    another_sample_id: str,
    sample_id_not_enough_reads: str,
    total_sequenced_reads_not_pass: int,
    sample_name: str,
) -> CGConfig:
    """Delivery API context."""
    status_db: Store = cg_context.status_db
    cg_context.housekeeper_api_ = delivery_housekeeper_api

    # Error case without samples
    helpers.add_case(status_db, internal_id=no_sample_case_id, name=no_sample_case_id)

    # Raredisease case with FASTQ and analysis as data delivery
    case_raredisease: Case = helpers.add_case(
        store=status_db,
        internal_id=case_id,
        name=case_name,
        data_analysis=Workflow.RAREDISEASE,
        data_delivery=DataDelivery.FASTQ_ANALYSIS_SCOUT,
    )

    # Microsalt case with FASTQ-QC as data delivery
    case_microsalt: Case = helpers.add_case(
        store=status_db,
        internal_id=another_case_id,
        name=another_case_name,
        data_analysis=Workflow.MICROSALT,
        data_delivery=DataDelivery.FASTQ_QC,
    )

    # Shared samples
    sample: Sample = helpers.add_sample(
        store=status_db,
        internal_id=sample_id,
        name=sample_name,
    )

    another_sample: Sample = helpers.add_sample(
        store=status_db,
        internal_id=another_sample_id,
        name=sample_name,
    )

    sample_not_enough_reads: Sample = helpers.add_sample(
        store=status_db,
        internal_id=sample_id_not_enough_reads,
        reads=total_sequenced_reads_not_pass,
    )

    # Raredisease samples
    for sample_raredisease in [sample, another_sample]:
        helpers.add_relationship(status_db, case=case_raredisease, sample=sample_raredisease)

    # Microsalt samples
    for sample_microsalt in [sample, another_sample, sample_not_enough_reads]:
        helpers.add_relationship(status_db, case=case_microsalt, sample=sample_microsalt)

    return cg_context
