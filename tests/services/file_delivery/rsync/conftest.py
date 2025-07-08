from pathlib import Path
from unittest.mock import create_autospec

import pytest

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.constants.constants import Workflow
from cg.constants.delivery import INBOX_NAME
from cg.constants.priority import SlurmAccount
from cg.models.cg_config import CGConfig
from cg.services.deliver_files.rsync.models import RsyncDeliveryConfig
from cg.services.deliver_files.rsync.service import DeliveryRsyncService
from cg.store.models import Case, Customer
from cg.store.store import Store


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


@pytest.fixture
def rsync_delivery_path() -> str:
    return "/a/delivery/path"


@pytest.fixture
def rsync_account() -> str:
    return SlurmAccount.DEVELOPMENT


@pytest.fixture
def rsync_base_path() -> str:
    return "/rsync/base/path"


@pytest.fixture
def rsync_destination_host() -> str:
    return "example.scilifelab.se"


@pytest.fixture
def inbox_path() -> str:
    return "/mnt/deliver"


@pytest.fixture
def rsync_destination_path(rsync_destination_host: str, inbox_path: str) -> str:
    return f"{rsync_destination_host}:{inbox_path}"


@pytest.fixture
def rsync_mail_user() -> str:
    return "some_user@scilifelab.se"


@pytest.fixture
def rsync_ticket() -> str:
    return "123456"


@pytest.fixture
def status_db_mock() -> Store:
    return create_autospec(Store)


@pytest.fixture
def customer_mock() -> Customer:
    return create_autospec(Customer, internal_id="test_customer_1")


@pytest.fixture
def case_mock(customer_mock: Customer, rsync_ticket: str) -> Case:
    return create_autospec(
        Case, customer=customer_mock, internal_id="some_internal_id", latest_ticket=rsync_ticket
    )


@pytest.fixture
def created_sbatch_information() -> str:
    return "a_string_with_sbatch_information"


@pytest.fixture
def first_job_number() -> int:
    return 1


@pytest.fixture
def second_job_number() -> int:
    return 2


@pytest.fixture
def slurm_api_mock(
    created_sbatch_information: str, first_job_number: int, second_job_number: int, mocker
) -> SlurmAPI:
    slurm_api_mock: SlurmAPI = create_autospec(SlurmAPI)
    slurm_api_mock.generate_sbatch_content.return_value = created_sbatch_information

    slurm_api_mock.submit_sbatch.side_effect = [first_job_number, second_job_number]

    mocker.patch("cg.services.deliver_files.rsync.service.SlurmAPI", return_value=slurm_api_mock)
    return slurm_api_mock


@pytest.fixture
def rsync_service(
    rsync_delivery_path: str,
    rsync_account: str,
    rsync_base_path: str,
    rsync_destination_path: str,
    rsync_mail_user: str,
    status_db_mock: Store,
) -> DeliveryRsyncService:
    return DeliveryRsyncService(
        delivery_path=rsync_delivery_path,
        rsync_config=RsyncDeliveryConfig(
            account=rsync_account,
            base_path=rsync_base_path,
            covid_destination_path="/covid/destination/path",
            covid_report_path="/covid/report/path",
            destination_path=rsync_destination_path,
            mail_user=rsync_mail_user,
        ),
        status_db=status_db_mock,
    )
