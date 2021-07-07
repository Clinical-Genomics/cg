import pytest

from cg.store import models
from cg.models.cg_config import CGConfig
from cgmodels.cg.constants import Pipeline


@pytest.fixture(name="mutant_case")
def fixture_mutant_case(
    cg_context: CGConfig, case_id: str, ticket_number: int, helpers
) -> models.Family:
    """Return mutant case"""
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id=case_id,
        case_id=ticket_number,
        data_analysis=Pipeline.SARS_COV_2,
    )
    return case


@pytest.fixture(name="microsalt_case")
def fixture_microsalt_case(
    cg_context: CGConfig, case_id: str, ticket_number: int, helpers
) -> models.Family:
    """Return mutant case"""
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id=case_id,
        case_id=ticket_number,
        data_analysis=Pipeline.MICROSALT,
    )
    return case
