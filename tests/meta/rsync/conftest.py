from pathlib import Path

import pytest

from cg.store.models import Family
from cg.models.cg_config import CGConfig
from cgmodels.cg.constants import Pipeline


@pytest.fixture(name="mutant_case")
def fixture_mutant_case(cg_context: CGConfig, case_id: str, ticket_id: str, helpers) -> Family:
    """Return mutant case"""
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id=case_id,
        name=ticket_id,
        data_analysis=Pipeline.SARS_COV_2,
    )
    return case


@pytest.fixture(name="microsalt_case")
def fixture_microsalt_case(cg_context: CGConfig, case_id: str, ticket_id: str, helpers) -> Family:
    """Return mutant case"""
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id=case_id,
        name=ticket_id,
        data_analysis=Pipeline.MICROSALT,
    )
    return case


@pytest.fixture(name="destination_path")
def fixture_destination_path() -> Path:
    """Retyrbs a dummy path."""
    return Path("path", "to", "destination")
