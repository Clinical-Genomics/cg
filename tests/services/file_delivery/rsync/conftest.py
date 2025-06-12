from pathlib import Path

import pytest
from cg.constants.delivery import INBOX_NAME

from cg.constants.constants import Workflow
from cg.models.cg_config import CGConfig
from cg.store.models import Case


@pytest.fixture
def mutant_case(cg_context: CGConfig, case_id: str, ticket_id: str, helpers) -> Case:
    """Return a Mutant case."""
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id=case_id,
        name=ticket_id,
        data_analysis=Workflow.MUTANT,
    )
    return case


@pytest.fixture
def microsalt_case(cg_context: CGConfig, case_id: str, ticket_id: str, helpers) -> Case:
    """Return a Microsalt case."""
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id=case_id,
        name=ticket_id,
        data_analysis=Workflow.MICROSALT,
    )
    return case


@pytest.fixture
def destination_path() -> Path:
    """Returns a dummy path."""
    return Path("path", "to", "destination")


@pytest.fixture
def all_samples_in_inbox(
    analysis_family: dict[str, any], dummy_file_name: str, tmpdir_factory, ticket_id: str
) -> Path:
    """Returns a customer inbox path with all samples delivered."""
    inbox = tmpdir_factory.mktemp(INBOX_NAME)
    for index in range(3):
        Path(inbox, ticket_id, analysis_family["samples"][index]["name"]).mkdir(
            exist_ok=True, parents=True
        )
        Path(inbox, ticket_id, analysis_family["samples"][index]["name"], dummy_file_name).touch(
            exist_ok=True
        )
    Path(inbox, ticket_id, analysis_family["name"]).mkdir(exist_ok=True, parents=True)
    Path(inbox, ticket_id, analysis_family["name"], dummy_file_name).touch(exist_ok=True)
    return Path(inbox, ticket_id)


@pytest.fixture
def folders_to_deliver(all_samples_in_inbox) -> set[Path]:
    return set(all_samples_in_inbox.iterdir())


@pytest.fixture
def dummy_file_name() -> str:
    """Returns a dummy file name."""
    return "dummy_file_name"
