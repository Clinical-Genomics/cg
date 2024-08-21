"""Delivery API context fixtures."""

from typing import Any

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import DataDelivery, Workflow
from cg.models.cg_config import CGConfig
from cg.store.models import Case, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture
def delivery_housekeeper_api(
    real_housekeeper_api: HousekeeperAPI,
    helpers: StoreHelpers,
    hk_delivery_sample_bundle: dict[str, Any],
    hk_delivery_another_sample_bundle: dict[str, Any],
    hk_delivery_case_bundle: dict[str, Any],
) -> HousekeeperAPI:
    """Delivery API Housekeeper context."""
    helpers.ensure_hk_bundle(
        store=real_housekeeper_api, bundle_data=hk_delivery_sample_bundle, include=True
    )
    helpers.ensure_hk_bundle(
        store=real_housekeeper_api, bundle_data=hk_delivery_another_sample_bundle, include=True
    )
    helpers.ensure_hk_bundle(
        store=real_housekeeper_api, bundle_data=hk_delivery_case_bundle, include=True
    )
    return real_housekeeper_api


@pytest.fixture
def delivery_store_balsamic(
    cg_context: CGConfig,
    helpers: StoreHelpers,
    no_sample_case_id: str,
    case_id: str,
    case_name: str,
    sample_id: str,
    another_sample_id: str,
    sample_name: str,
    another_sample_name: str,
    wgs_application_tag: str,
) -> Store:
    """Delivery API StatusDB context for Balsamic."""
    status_db: Store = cg_context.status_db

    # Error case without samples
    helpers.add_case(store=status_db, internal_id=no_sample_case_id, name=no_sample_case_id)

    # Balsamic case with FASTQ and analysis as data delivery
    case: Case = helpers.add_case(
        store=status_db,
        internal_id=case_id,
        name=case_name,
        data_analysis=Workflow.BALSAMIC,
        data_delivery=DataDelivery.FASTQ_ANALYSIS_SCOUT,
    )

    # Balsamic samples
    sample: Sample = helpers.add_sample(
        store=status_db,
        application_tag=wgs_application_tag,
        internal_id=sample_id,
        name=sample_name,
    )

    another_sample: Sample = helpers.add_sample(
        store=status_db,
        application_tag=wgs_application_tag,
        internal_id=another_sample_id,
        name=another_sample_name,
    )

    for sample_balsamic in [sample, another_sample]:
        helpers.add_relationship(store=status_db, case=case, sample=sample_balsamic)

    return status_db


@pytest.fixture
def delivery_store_microsalt(
    cg_context: CGConfig,
    helpers: StoreHelpers,
    case_id: str,
    no_sample_case_id: str,
    case_name: str,
    sample_id: str,
    another_sample_id: str,
    sample_id_not_enough_reads: str,
    total_sequenced_reads_pass: int,
    total_sequenced_reads_not_pass: int,
    sample_name: str,
    another_sample_name: str,
    microbial_application_tag: str,
) -> Store:
    """Delivery API StatusDB context for MicroSALT."""
    status_db: Store = cg_context.status_db

    # Error case without samples
    helpers.add_case(store=status_db, internal_id=no_sample_case_id, name=no_sample_case_id)

    # MicroSALT case with FASTQ-QC as data delivery
    case: Case = helpers.add_case(
        store=status_db,
        internal_id=case_id,
        name=case_name,
        data_analysis=Workflow.MICROSALT,
        data_delivery=DataDelivery.FASTQ_QC,
    )

    # MicroSALT samples
    sample: Sample = helpers.add_sample(
        store=status_db,
        application_tag=microbial_application_tag,
        internal_id=sample_id,
        name=sample_name,
        reads=total_sequenced_reads_pass,
    )

    another_sample: Sample = helpers.add_sample(
        store=status_db,
        application_tag=microbial_application_tag,
        internal_id=another_sample_id,
        name=another_sample_name,
        reads=total_sequenced_reads_pass,
    )

    sample_not_enough_reads: Sample = helpers.add_sample(
        store=status_db,
        application_tag=microbial_application_tag,
        internal_id=sample_id_not_enough_reads,
        reads=total_sequenced_reads_not_pass,
    )

    for sample_microsalt in [sample, another_sample, sample_not_enough_reads]:
        helpers.add_relationship(store=status_db, case=case, sample=sample_microsalt)

    return status_db


@pytest.fixture
def delivery_context_balsamic(
    cg_context: CGConfig,
    delivery_housekeeper_api: HousekeeperAPI,
    delivery_store_balsamic: Store,
) -> CGConfig:
    """Delivery API Balsamic context."""
    cg_context.housekeeper_api_ = delivery_housekeeper_api
    cg_context.status_db_ = delivery_store_balsamic
    return cg_context


@pytest.fixture
def delivery_context_microsalt(
    cg_context: CGConfig,
    delivery_housekeeper_api: HousekeeperAPI,
    delivery_store_microsalt: Store,
) -> CGConfig:
    """Delivery API MicroSALT context."""
    cg_context.housekeeper_api_ = delivery_housekeeper_api
    cg_context.status_db_ = delivery_store_microsalt
    return cg_context
