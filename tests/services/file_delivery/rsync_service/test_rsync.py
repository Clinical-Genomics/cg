"""Tests for rsync API"""

import logging
import shutil
from pathlib import Path

import pytest

from cg.constants import Workflow
from cg.constants.priority import SlurmAccount, SlurmQos
from cg.exc import CgError
from cg.services.deliver_files.rsync.service import (
    DeliveryRsyncService,
)
from cg.store.models import Case
from cg.store.store import Store
from tests.store.conftest import case_obj


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


def test_run_rsync_on_slurm(
    microsalt_case: Case,
    delivery_rsync_service: DeliveryRsyncService,
    ticket_id: str,
    caplog,
    mocker,
    helpers,
):
    """Test for running rsync using SLURM."""
    caplog.set_level(logging.INFO)

    # GIVEN a valid microsalt case
    case: Case = microsalt_case

    # GIVEN paths needed to run rsync
    mocker.patch.object(DeliveryRsyncService, "get_source_and_destination_paths")
    DeliveryRsyncService.get_source_and_destination_paths.return_value = {
        "delivery_source_path": Path("/path/to/source"),
        "rsync_destination_path": Path("/path/to/destination"),
    }

    mocker.patch.object(DeliveryRsyncService, "get_all_cases_from_ticket")
    DeliveryRsyncService.get_all_cases_from_ticket.return_value = [case]

    # WHEN the destination path is created
    sbatch_number: int = delivery_rsync_service.run_rsync_for_ticket(ticket=ticket_id, dry_run=True)

    # THEN check that SARS-COV-2 analysis is not delivered
    assert "Delivering report for SARS-COV-2 analysis" not in caplog.text

    # THEN check that an integer was returned as sbatch number
    assert isinstance(sbatch_number, int)


def test_run_rsync_on_slurm_no_cases(
    delivery_rsync_service: DeliveryRsyncService, ticket_id: str, caplog, mocker, helpers
):
    """Test for running rsync using SLURM when there are no cases on the ticket."""
    caplog.set_level(logging.INFO)

    # GIVEN ticket without any cases
    mocker.patch.object(DeliveryRsyncService, "get_all_cases_from_ticket")
    DeliveryRsyncService.get_all_cases_from_ticket.return_value = None

    # WHEN the job is submitted

    # THEN an error is raised
    with pytest.raises(CgError):
        delivery_rsync_service.run_rsync_for_ticket(ticket=ticket_id, dry_run=True)


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
    delivery_rsync_service.covid_destination_path = covid_destination_path

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


def test_slurm_rsync_single_case(
    all_samples_in_inbox: Path,
    case: Case,
    destination_path: Path,
    delivery_rsync_service: DeliveryRsyncService,
    caplog,
    mocker,
    ticket_id: str,
    folders_to_deliver: set[Path],
):
    """Test for running rsync on a single case using SLURM."""
    caplog.set_level(logging.INFO)

    # GIVEN paths needed to run rsync
    mocker.patch.object(DeliveryRsyncService, "get_source_and_destination_paths")
    DeliveryRsyncService.get_source_and_destination_paths.return_value = {
        "delivery_source_path": all_samples_in_inbox,
        "rsync_destination_path": destination_path,
    }

    mocker.patch.object(Store, "get_latest_ticket_from_case")
    Store.get_latest_ticket_from_case.return_value = ticket_id

    # WHEN the destination path is created
    sbatch_number: int
    is_complete_delivery: bool
    sbatch_number: int = delivery_rsync_service.run_rsync_for_case(
        case=case,
        dry_run=True,
        folders_to_deliver=folders_to_deliver,
    )

    # THEN check that an integer was returned as sbatch number and the delivery should be complete
    assert isinstance(sbatch_number, int)


def test_slurm_rsync_single_case_missing_file(
    all_samples_in_inbox: Path,
    case: Case,
    destination_path: Path,
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
        "rsync_destination_path": destination_path,
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
