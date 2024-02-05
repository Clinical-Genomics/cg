from pathlib import Path

import pytest

from cg.constants.constants import Workflow
from cg.models.cg_config import CGConfig
from cg.store.models import Case


@pytest.fixture
def mutant_case(cg_context: CGConfig, case_id: str, ticket_id: str, helpers) -> Case:
    """Return mutant case"""
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id=case_id,
        name=ticket_id,
        data_analysis=Workflow.MUTANT,
    )
    return case


@pytest.fixture
def microsalt_case(cg_context: CGConfig, case_id: str, ticket_id: str, helpers) -> Case:
    """Return mutant case"""
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id=case_id,
        name=ticket_id,
        data_analysis=Workflow.MICROSALT,
    )
    return case


@pytest.fixture
def destination_path() -> Path:
    """Retyrbs a dummy path."""
    return Path("path", "to", "destination")
