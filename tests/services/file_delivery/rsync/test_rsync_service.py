"""Tests for rsync API"""

import logging
import shutil
from pathlib import Path
from typing import cast
from unittest.mock import ANY, call, create_autospec

import pytest

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.constants import Workflow
from cg.constants.priority import SlurmAccount, SlurmQos
from cg.exc import CgError
from cg.models.slurm.sbatch import Sbatch
from cg.services.deliver_files.rsync.models import RsyncDeliveryConfig
from cg.services.deliver_files.rsync.service import DeliveryRsyncService
from cg.store.models import Case, Customer
from cg.store.store import Store


def test_get_source_and_destination_paths(
    mutant_case: Case, delivery_rsync_service: DeliveryRsyncService, ticket_id: str, mocker
):
    """Test generating the source path before rsync."""

    # GIVEN a valid Sars-cov-2 case
    case = mutant_case

    # GIVEN file exists
    mocker.patch.object(DeliveryRsyncService, "get_all_cases_from_ticket")
    DeliveryRsyncService.get_all_cases_from_ticket.return_value = [case]

    # WHEN the source path is created
    source_and_destination_paths = delivery_rsync_service.get_source_and_destination_paths(
        ticket=ticket_id, customer_internal_id=case.customer.internal_id
    )

    # THEN the source path ends with a customer id, followed by "inbox" and a ticket_id id
    assert (
        source_and_destination_paths["delivery_source_path"]
        .as_posix()
        .endswith(f"/cust000/inbox/{ticket_id}")
    )
    # THEN the destination path is in the format server.name.se:/path/cust_id/path/ticket_id/
    assert (
        source_and_destination_paths["rsync_destination_path"].as_posix()
        == "server.name.se:/some/cust000/inbox"
    )


def test_set_log_dir(delivery_rsync_service: DeliveryRsyncService, ticket_id: str, caplog):
    """Test function to set log dir for path."""

    caplog.set_level(logging.INFO)

    # GIVEN an DeliveryRsyncService, with its base path as its log dir
    base_path: Path = delivery_rsync_service.log_dir

    # WHEN setting the log directory
    delivery_rsync_service.set_log_dir(folder_prefix=ticket_id)

    # THEN the log dir should set to a new path, different from the base path
    assert base_path.as_posix() != delivery_rsync_service.log_dir.as_posix()
    assert "Setting log dir to:" in caplog.text


def test_make_log_dir(delivery_rsync_service: DeliveryRsyncService, ticket_id: str, caplog):
    """Test generating the directory for logging."""
    caplog.set_level(logging.INFO)

    # WHEN the log directory is created
    delivery_rsync_service.set_log_dir(folder_prefix=ticket_id)
    delivery_rsync_service.create_log_dir(dry_run=True)

    # THEN the path is not created since it is a dry run
    assert "Would have created path" in caplog.text

    # THEN the created path is
    assert str(delivery_rsync_service.log_dir).startswith(f"/another/path/{ticket_id}")


@pytest.mark.freeze_time("2025-06-11 10:05:01")
def test_run_rsync_on_slurm_for_ticket(
    case_mock: Case,
    rsync_service: DeliveryRsyncService,
    status_db_mock: Store,
    slurm_api_mock: SlurmAPI,
    created_sbatch_information,
    first_job_number,
    rsync_mail_user: str,
    rsync_base_path: str,
    rsync_delivery_path: str,
    rsync_destination_path: str,
):
    # GIVEN a valid case related to a customer and a ticket
    customer: Customer = case_mock.customer
    ticket: str = cast(str, case_mock.latest_ticket)

    # GIVEN the case is associated with the given ticket
    status_db_mock.get_cases_by_ticket_id.return_value = [case_mock]

    # GIVEN a DeliveryRsyncService with the slurm production account
    rsync_service.account = SlurmAccount.PRODUCTION

    # WHEN rsync is run for a ticket
    returned_sbatch_number: int = rsync_service.run_rsync_for_ticket(ticket=ticket, dry_run=True)

    # THEN the correct sbatch content is generated
    expected_command: str = (
        f"\nrsync -rvL {rsync_delivery_path}/{customer.internal_id}/inbox/{ticket} "
        f"{rsync_destination_path}/{customer.internal_id}/inbox\n"
    )

    slurm_api_mock.generate_sbatch_content.assert_called_with(
        sbatch_parameters=Sbatch(
            account=SlurmAccount.PRODUCTION,
            commands=expected_command,
            email=rsync_mail_user,
            error='\necho "Rsync failed"\n',
            exclude="--exclude=gpu-compute-0-[0-1],cg-dragen",
            hours=24,
            job_name=f"{ticket}_rsync",
            log_dir=f"{rsync_base_path}/{ticket}_250611_10_05_01_000000",
            memory=1,
            minutes="00",
            number_tasks=1,
            quality_of_service=SlurmQos.HIGH,
            use_login_shell="",
        )
    )

    # THEN the correct sbatch is submitted
    slurm_api_mock.submit_sbatch.assert_called_with(
        sbatch_content=created_sbatch_information,
        sbatch_path=Path(f"{rsync_base_path}/{ticket}_250611_10_05_01_000000/{ticket}_rsync.sh"),
    )

    # THEN the created job number is returned
    assert returned_sbatch_number == first_job_number


def test_run_rsync_on_slurm_no_cases(
    rsync_service: DeliveryRsyncService,
    status_db_mock,
    rsync_ticket: str,
):
    """Test for running rsync using SLURM when there are no cases on the ticket."""

    # GIVEN ticket without any cases
    status_db_mock.get_cases_by_ticket_id.return_value = []

    # WHEN the job is submitted
    with pytest.raises(CgError):
        # THEN an error is raised
        rsync_service.run_rsync_for_ticket(ticket=rsync_ticket, dry_run=True)


def test_concatenate_rsync_commands(
    analysis_family: dict,
    analysis_store_trio,
    case: Case,
    customer_id,
    folders_to_deliver: set[Path],
    project_dir,
    delivery_rsync_service: DeliveryRsyncService,
    ticket_id: str,
):
    """Tests the function to concatenate rsync commands for transferring multiple files."""
    # GIVEN a list with a case and a sample name

    source_and_destination_paths = {
        "delivery_source_path": Path(project_dir, customer_id, ticket_id),
        "rsync_destination_path": Path(project_dir, customer_id),
    }
    # WHEN then commands are generated
    command: str = delivery_rsync_service.concatenate_rsync_commands(
        folder_list=folders_to_deliver,
        source_and_destination_paths=source_and_destination_paths,
        ticket=ticket_id,
        case=case,
    )
    # THEN the correct folder should be added to the source path
    assert (
        " ".join(
            [
                str(source_and_destination_paths["delivery_source_path"] / analysis_family["name"]),
                str(source_and_destination_paths["delivery_source_path"]),
            ]
        )
        in command
    )
    assert (
        " ".join(
            [
                str(
                    source_and_destination_paths["delivery_source_path"]
                    / analysis_family["samples"][0]["name"]
                ),
                str(source_and_destination_paths["delivery_source_path"]),
            ]
        )
        in command
    )


def test_concatenate_rsync_commands_mutant(
    analysis_family: dict,
    analysis_store_trio,
    case: Case,
    customer_id,
    folders_to_deliver: set[Path],
    mocker,
    project_dir,
    delivery_rsync_service: DeliveryRsyncService,
    ticket_id: str,
):
    """Tests the function to concatenate Rsync commands for transferring multiple files."""
    # GIVEN a list with a Mutant case and a sample name and a Mutant report file
    case.data_analysis = Workflow.MUTANT
    source_and_destination_paths = {
        "delivery_source_path": Path(project_dir, customer_id, ticket_id),
        "rsync_destination_path": Path(project_dir, customer_id),
    }
    report_path = Path(project_dir, customer_id, ticket_id, "a_report_file")
    covid_destination_path = Path(project_dir, "destination")
    delivery_rsync_service.covid_destination_path = covid_destination_path.as_posix()

    # WHEN then commands are generated
    mocker.patch.object(DeliveryRsyncService, "format_covid_report_path", return_value=report_path)
    mocker.patch.object(
        DeliveryRsyncService, "format_covid_destination_path", return_value=covid_destination_path
    )
    command: str = delivery_rsync_service.concatenate_rsync_commands(
        folder_list=folders_to_deliver,
        source_and_destination_paths=source_and_destination_paths,
        ticket=ticket_id,
        case=case,
    )

    # THEN the correct folder should be added to the source path
    assert report_path.name in command
    assert covid_destination_path.as_posix() in command


@pytest.mark.freeze_time("2025-06-11 10:05:01")
def test_slurm_rsync_single_case(
    case_mock: Case,
    created_sbatch_information: str,
    rsync_destination_host: str,
    inbox_path: str,
    first_job_number: int,
    second_job_number: int,
    rsync_base_path: str,
    rsync_delivery_path: str,
    rsync_destination_path: str,
    rsync_mail_user: str,
    rsync_service: DeliveryRsyncService,
    folders_to_deliver: set[Path],
    slurm_api_mock: SlurmAPI,
):
    """Test for running rsync on a single case using SLURM."""
    # GIVEN a valid case, related to a customer and ticket exists
    customer: Customer = case_mock.customer
    ticket: str = cast(str, case_mock.latest_ticket)

    # WHEN run_rsync_for_case is run
    sbatch_number: int = rsync_service.run_rsync_for_case(
        case=case_mock,
        dry_run=True,
        folders_to_deliver=folders_to_deliver,
    )

    # THEN two jobs are created with the correct commands and parameters
    _, first_call_kwargs = slurm_api_mock.generate_sbatch_content.call_args_list[0]
    _, second_call_kwargs = slurm_api_mock.generate_sbatch_content.call_args_list[1]

    sbatch_first_job: Sbatch = first_call_kwargs["sbatch_parameters"]
    sbatch_second_job: Sbatch = second_call_kwargs["sbatch_parameters"]

    expected_create_inbox_command = f"""
ssh {rsync_destination_host} "mkdir -p {inbox_path}/{customer.internal_id}/inbox/{ticket}"
"""

    assert sbatch_first_job == Sbatch(
        job_name=f"{ticket}_create_inbox",
        number_tasks=1,
        memory=1,
        account=rsync_service.account,
        log_dir=f"{rsync_base_path}/{case_mock.internal_id}_250611_10_05_01_000000",
        email=rsync_mail_user,
        hours=24,
        quality_of_service=SlurmQos.LOW,
        commands=expected_create_inbox_command,
        error='\necho "Create inbox failed"\n',
    )

    assert sbatch_second_job.job_name == f"{case_mock.internal_id}_rsync"
    assert sbatch_second_job.dependency == f"--dependency=afterok:{first_job_number}"

    expected_rsync_commands: list[str] = [
        (
            f"rsync -rvL {rsync_delivery_path}/{customer.internal_id}/inbox/{ticket}/{type} "
            f"{rsync_destination_path}/{customer.internal_id}/inbox/{ticket}"
        )
        for type in ["case", "father", "mother", "child"]
    ]

    for command in expected_rsync_commands:
        assert command in sbatch_second_job.commands

    # THEN both job are correctly submitted
    first_call, second_call = slurm_api_mock.submit_sbatch.mock_calls

    assert first_call == call(
        sbatch_content=created_sbatch_information,
        sbatch_path=Path(
            f"{rsync_base_path}/{case_mock.internal_id}_250611_10_05_01_000000/{ticket}_create_inbox.sh"
        ),
    )

    assert second_call == call(
        sbatch_content=created_sbatch_information,
        sbatch_path=Path(
            f"{rsync_base_path}/{case_mock.internal_id}_250611_10_05_01_000000/{case_mock.internal_id}_rsync.sh"
        ),
    )

    # THEN the created job number of the file transfer job is returned
    assert sbatch_number == second_job_number


def test_slurm_rsync_single_case_no_ticket(
    folders_to_deliver: set[Path], rsync_service: DeliveryRsyncService
):
    # GIVEN the rsync service and a case with no related ticket
    case_with_no_ticket: Case = create_autospec(Case, latest_ticket=None)

    # WHEN run_rsync_for_case is called with the case
    with pytest.raises(CgError):
        # THEN an exception is thrown
        rsync_service.run_rsync_for_case(
            case=case_with_no_ticket, dry_run=True, folders_to_deliver=folders_to_deliver
        )


def test_slurm_rsync_single_case_missing_file(
    all_samples_in_inbox: Path,
    case: Case,
    rsync_destination_path: Path,
    delivery_rsync_service: DeliveryRsyncService,
    caplog,
    mocker,
    ticket_id: str,
    folders_to_deliver: set[Path],
):
    """Test for running rsync on a single case with a missing file using SLURM."""
    caplog.set_level(logging.INFO)

    # GIVEN a valid mip case and sample folder missing
    shutil.rmtree(Path(all_samples_in_inbox, case.links[0].sample.name))

    # GIVEN paths needed to run rsync
    mocker.patch.object(DeliveryRsyncService, "get_source_and_destination_paths")
    DeliveryRsyncService.get_source_and_destination_paths.return_value = {
        "delivery_source_path": all_samples_in_inbox,
        "rsync_destination_path": Path(rsync_destination_path),
    }

    mocker.patch.object(Store, "get_latest_ticket_from_case")
    Store.get_latest_ticket_from_case.return_value = ticket_id

    # WHEN the destination path is created
    sbatch_number: int

    sbatch_number: int = delivery_rsync_service.run_rsync_for_case(
        case=case, dry_run=True, folders_to_deliver=folders_to_deliver
    )

    # THEN check that an integer was returned as sbatch number
    assert isinstance(sbatch_number, int)


def test_slurm_quality_of_service_production(delivery_rsync_service: DeliveryRsyncService):
    # GIVEN an DeliveryRsyncService instance

    # WHEN the account of the api is set to production
    delivery_rsync_service.account = SlurmAccount.PRODUCTION

    # THEN the quality of service should be set to HIGH
    assert delivery_rsync_service.slurm_quality_of_service == SlurmQos.HIGH


def test_slurm_quality_of_service_other(delivery_rsync_service: DeliveryRsyncService):
    # GIVEN an DeliveryRsyncService instance

    # WHEN the account of the api is set to development
    delivery_rsync_service.account = SlurmAccount.DEVELOPMENT

    # THEN the quality of service should be set to LOW
    assert delivery_rsync_service.slurm_quality_of_service == SlurmQos.LOW
