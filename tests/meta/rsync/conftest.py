from pathlib import Path

import pytest

from cg.constants.constants import Pipeline
from cg.models.cg_config import CGConfig
from cg.store.models import Case


@pytest.fixture
def mutant_case(cg_context: CGConfig, case_id: str, ticket_id: str, helpers) -> Case:
    """Return mutant case"""
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id=case_id,
        name=ticket_id,
        data_analysis=Pipeline.SARS_COV_2,
    )
    return case


@pytest.fixture
def microsalt_case(cg_context: CGConfig, case_id: str, ticket_id: str, helpers) -> Case:
    """Return mutant case"""
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id=case_id,
        name=ticket_id,
        data_analysis=Pipeline.MICROSALT,
    )
    return case


@pytest.fixture
def destination_path() -> Path:
    """Retyrbs a dummy path."""
    return Path("path", "to", "destination")
