"""Tests for rsync API"""

import logging
import shutil
from pathlib import Path

import pytest

from cg.constants.priority import SlurmAccount, SlurmQos
from cg.exc import CgError
from cg.meta.rsync import RsyncAPI
from cg.store.models import Case
from cg.store.store import Store
from tests.meta.deliver.conftest import all_samples_in_inbox, dummy_file_name
from tests.store.conftest import case_obj


def test_get_source_and_destination_paths(
    mutant_case: Case, rsync_api: RsyncAPI, ticket_id: str, mocker
):
    """Test generating the source path before rsync."""

    # GIVEN a valid Sars-cov-2 case
    case = mutant_case

    # GIVEN file exists
    mocker.patch.object(RsyncAPI, "get_all_cases_from_ticket")
    RsyncAPI.get_all_cases_from_ticket.return_value = [case]

    # WHEN the source path is created
    source_and_destination_paths = rsync_api.get_source_and_destination_paths(
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


def test_set_log_dir(rsync_api: RsyncAPI, ticket_id: str, caplog):
    """Test function to set log dir for path."""

    caplog.set_level(logging.INFO)

    # GIVEN an RsyncAPI, with its base path as its log dir
    base_path: Path = rsync_api.log_dir

    # WHEN setting the log directory
    rsync_api.set_log_dir(folder_prefix=ticket_id)

    # THEN the log dir should set to a new path, different from the base path
    assert base_path.as_posix() != rsync_api.log_dir.as_posix()
    assert "Setting log dir to:" in caplog.text


def test_make_log_dir(rsync_api: RsyncAPI, ticket_id: str, caplog):
    """Test generating the directory for logging."""
    caplog.set_level(logging.INFO)

    # WHEN the log directory is created
    rsync_api.set_log_dir(folder_prefix=ticket_id)
    rsync_api.create_log_dir(dry_run=True)

    # THEN the path is not created since it is a dry run
    assert "Would have created path" in caplog.text

    # THEN the created path is
    assert str(rsync_api.log_dir).startswith(f"/another/path/{ticket_id}")


def test_run_rsync_on_slurm(
    microsalt_case: Case, rsync_api: RsyncAPI, ticket_id: str, caplog, mocker, helpers
):
    """Test for running rsync using SLURM."""
    caplog.set_level(logging.INFO)

    # GIVEN a valid microsalt case
    case: Case = microsalt_case

    # GIVEN paths needed to run rsync
    mocker.patch.object(RsyncAPI, "get_source_and_destination_paths")
    RsyncAPI.get_source_and_destination_paths.return_value = {
        "delivery_source_path": Path("/path/to/source"),
        "rsync_destination_path": Path("/path/to/destination"),
    }

    mocker.patch.object(RsyncAPI, "get_all_cases_from_ticket")
    RsyncAPI.get_all_cases_from_ticket.return_value = [case]

    # WHEN the destination path is created
    sbatch_number: int = rsync_api.run_rsync_on_slurm(ticket=ticket_id, dry_run=True)

    # THEN check that SARS-COV-2 analysis is not delivered
    assert "Delivering report for SARS-COV-2 analysis" not in caplog.text

    # THEN check that an integer was returned as sbatch number
    assert isinstance(sbatch_number, int)


def test_run_rsync_on_slurm_no_cases(rsync_api: RsyncAPI, ticket_id: str, caplog, mocker, helpers):
    """Test for running rsync using SLURM when there are no cases on the ticket."""
    caplog.set_level(logging.INFO)

    # GIVEN ticket without any cases
    mocker.patch.object(RsyncAPI, "get_all_cases_from_ticket")
    RsyncAPI.get_all_cases_from_ticket.return_value = None

    # WHEN the job is submitted
    with pytest.raises(CgError):
        rsync_api.run_rsync_on_slurm(ticket=ticket_id, dry_run=True)

        # THEN check that error is raised based on no cases being present
        assert "Could not find any cases for ticket" in caplog.text


def test_get_folders_to_deliver(
    analysis_family: dict, analysis_store_trio, rsync_api: RsyncAPI, case_id: str
):
    """Tests the ability for the rsync api to get case and sample names."""
    # GIVEN a case

    # WHEN the function gets the folders
    folder_list: list[str] = rsync_api.get_folders_to_deliver(
        case_id=case_id, sample_files_present=True, case_files_present=True
    )

    # THEN it the list should contain the case name and all the samples
    assert folder_list == [
        analysis_family["samples"][0]["name"],
        analysis_family["samples"][1]["name"],
        analysis_family["samples"][2]["name"],
        analysis_family["name"],
    ]


def test_concatenate_rsync_commands(
    analysis_family: dict, analysis_store_trio, project_dir, customer_id, ticket_id: str
):
    """Tests the function to concatenate rsync commands for transferring multiple files."""
    # GIVEN a list with a case and a sample name
    folder_list: list[str] = [analysis_family["name"], analysis_family["samples"][0]["name"]]
    source_and_destination_paths = {
        "delivery_source_path": project_dir / customer_id / ticket_id,
        "rsync_destination_path": project_dir / customer_id,
    }
    # WHEN then commands are generated
    commands: str = RsyncAPI.concatenate_rsync_commands(
        folder_list=folder_list,
        source_and_destination_paths=source_and_destination_paths,
        ticket=ticket_id,
    )
    # THEN the correct folder should be added to the source path
    assert (
        " ".join(
            [
                str(source_and_destination_paths["delivery_source_path"] / analysis_family["name"]),
                str(source_and_destination_paths["delivery_source_path"]),
            ]
        )
        in commands
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
        in commands
    )


def test_slurm_rsync_single_case(
    all_samples_in_inbox: Path,
    case: Case,
    destination_path: Path,
    rsync_api: RsyncAPI,
    caplog,
    mocker,
    ticket_id: str,
):
    """Test for running rsync on a single case using SLURM."""
    caplog.set_level(logging.INFO)

    # GIVEN paths needed to run rsync
    mocker.patch.object(RsyncAPI, "get_source_and_destination_paths")
    RsyncAPI.get_source_and_destination_paths.return_value = {
        "delivery_source_path": all_samples_in_inbox,
        "rsync_destination_path": destination_path,
    }

    mocker.patch.object(Store, "get_latest_ticket_from_case")
    Store.get_latest_ticket_from_case.return_value = ticket_id

    # WHEN the destination path is created
    sbatch_number: int
    is_complete_delivery: bool
    is_complete_delivery, sbatch_number = rsync_api.slurm_rsync_single_case(
        case=case,
        case_files_present=True,
        dry_run=True,
        sample_files_present=True,
    )

    # THEN check that an integer was returned as sbatch number and the delivery should be complete
    assert isinstance(sbatch_number, int)
    assert is_complete_delivery


def test_slurm_rsync_single_case_missing_file(
    all_samples_in_inbox: Path,
    case: Case,
    destination_path: Path,
    rsync_api: RsyncAPI,
    caplog,
    mocker,
    ticket_id: str,
):
    """Test for running rsync on a single case with a missing file using SLURM."""
    caplog.set_level(logging.INFO)

    # GIVEN a valid mip case and sample folder missing
    shutil.rmtree(Path(all_samples_in_inbox, case.links[0].sample.name))

    # GIVEN paths needed to run rsync
    mocker.patch.object(RsyncAPI, "get_source_and_destination_paths")
    RsyncAPI.get_source_and_destination_paths.return_value = {
        "delivery_source_path": all_samples_in_inbox,
        "rsync_destination_path": destination_path,
    }

    mocker.patch.object(Store, "get_latest_ticket_from_case")
    Store.get_latest_ticket_from_case.return_value = ticket_id

    # WHEN the destination path is created
    sbatch_number: int
    is_complete_delivery: bool
    is_complete_delivery, sbatch_number = rsync_api.slurm_rsync_single_case(
        case=case,
        case_files_present=True,
        dry_run=True,
        sample_files_present=True,
    )

    # THEN check that an integer was returned as sbatch number
    assert isinstance(sbatch_number, int)
    assert not is_complete_delivery


def test_slurm_quality_of_service_production(rsync_api: RsyncAPI):
    # GIVEN an RsyncAPI instance

    # WHEN the account of the api is set to production
    rsync_api.account = SlurmAccount.PRODUCTION

    # THEN the quality of service should be set to HIGH
    assert rsync_api.slurm_quality_of_service == SlurmQos.HIGH


def test_slurm_quality_of_service_other(rsync_api: RsyncAPI):
    # GIVEN an RsyncAPI instance

    # WHEN the account of the api is set to development
    rsync_api.account = SlurmAccount.DEVELOPMENT

    # THEN the quality of service should be set to LOW
    assert rsync_api.slurm_quality_of_service == SlurmQos.LOW
