import datetime
from unittest import mock

import pytest
from click.testing import CliRunner
from housekeeper.store.models import Archive, File
from requests import Response

from cg.cli.archive import archive_spring_files, update_job_statuses
from cg.constants import EXIT_SUCCESS
from cg.io.controller import APIRequest
from cg.meta.archive.ddn_dataflow import (
    FAILED_JOB_STATUSES,
    ONGOING_JOB_STATUSES,
    AuthToken,
    GetJobStatusPayload,
    GetJobStatusResponse,
    JobStatus,
    TransferJob,
    TransferPayload,
)
from cg.models.cg_config import CGConfig


def test_limit_and_archive_all_fails(cli_runner: CliRunner, cg_context: CGConfig):
    """Tests that when invoking archive-spring-files in the Archive CLI module, the command is aborted
    if both a limit and the --archive-all flag is provided."""

    # GIVEN a CLI runner and a context

    # WHEN invoking archive_spring_files with both a given limit and specifying archive_all
    result = cli_runner.invoke(
        archive_spring_files,
        ["--limit", 100, "--archive-all"],
        obj=cg_context,
    )

    # THEN the command should have exited with an exit_code 1
    assert result.exit_code == 1
    assert (
        "Incorrect input parameters - please do not provide both a limit and set --archive-all."
        in result.stdout
    )


def test_archive_spring_files_success(
    cli_runner: CliRunner,
    archive_context: CGConfig,
    archival_job_id: int,
    test_auth_token: AuthToken,
    ok_miria_response: Response,
):
    """Tests that the CLI command 'cg archive archive-spring-files' adds an archive with the correct job_id when
    an archiving job is launched via Miria."""

    # GIVEN a CLI runner and a context

    # GIVEN a spring file belonging to a customer with archive location 'karolinska_bucket'
    all_non_archived_spring_files: list[
        File
    ] = archive_context.housekeeper_api.get_non_archived_spring_files()
    assert len(all_non_archived_spring_files) == 1
    spring_file: File = all_non_archived_spring_files[0]

    # WHEN running 'cg archive archive-spring-files'
    with mock.patch.object(
        AuthToken,
        "model_validate",
        return_value=test_auth_token,
    ), mock.patch.object(
        APIRequest,
        "api_request_from_content",
        return_value=ok_miria_response,
    ), mock.patch.object(
        TransferPayload, "post_request", return_value=TransferJob(jobId=archival_job_id)
    ):
        result = cli_runner.invoke(
            archive_spring_files,
            obj=archive_context,
        )

    # THEN the command should have executed without fail and added an entry in the archive with the archiving task id
    # returned by Miria
    assert result.exit_code == EXIT_SUCCESS
    assert spring_file.archive.archiving_task_id == archival_job_id


@pytest.mark.parametrize(
    "job_status", [JobStatus.COMPLETED, FAILED_JOB_STATUSES[0], ONGOING_JOB_STATUSES[0]]
)
def test_get_archival_job_status(
    cli_runner: CliRunner,
    archive_context: CGConfig,
    archival_job_id: int,
    test_auth_token: AuthToken,
    ok_miria_response: Response,
    job_status: JobStatus,
):
    """Tests that when invoking update_job_statuses in the Archive CLI module with an ongoing archival job,
    the database is updated according to whether the job has completed, failed or is still ongoing.
    """

    # GIVEN a CLI runner and a context

    # GIVEN an archive entry with an ongoing archival
    assert len(archive_context.housekeeper_api.get_archive_entries()) == 1

    # WHEN invoking update_job_statuses
    with mock.patch.object(
        AuthToken,
        "model_validate",
        return_value=test_auth_token,
    ), mock.patch.object(
        APIRequest,
        "api_request_from_content",
        return_value=ok_miria_response,
    ), mock.patch.object(
        GetJobStatusPayload,
        "get_job_status",
        return_value=GetJobStatusResponse(id=archival_job_id, status=job_status),
    ):
        result = cli_runner.invoke(
            update_job_statuses,
            obj=archive_context,
        )

    # THEN the command should have exited successfully and updated the archive record
    assert result.exit_code == 0
    if job_status == JobStatus.COMPLETED:
        assert archive_context.housekeeper_api.get_archive_entries(
            archival_task_id=archival_job_id
        )[0].archived_at
    elif job_status in FAILED_JOB_STATUSES:
        assert not archive_context.housekeeper_api.get_archive_entries(
            archival_task_id=archival_job_id
        )
    elif job_status in ONGOING_JOB_STATUSES:
        assert not archive_context.housekeeper_api.get_archive_entries(
            archival_task_id=archival_job_id
        )[0].archived_at


@pytest.mark.parametrize(
    "job_status", [JobStatus.COMPLETED, FAILED_JOB_STATUSES[0], ONGOING_JOB_STATUSES[0]]
)
def test_get_retrieval_job_status(
    cli_runner: CliRunner,
    archive_context: CGConfig,
    retrieval_job_id: int,
    test_auth_token: AuthToken,
    ok_miria_response: Response,
    job_status: JobStatus,
):
    """Tests that when invoking update_job_statuses in the Archive CLI module with an ongoing retrieval job,
    the database is updated according to whether the job has completed, failed or is still ongoing.
    """

    # GIVEN a CLI runner and a context

    # GIVEN an archive entry with an ongoing retrieval
    retrieving_archive: Archive = archive_context.housekeeper_api.get_archive_entries()[0]
    retrieving_archive.archived_at = datetime.datetime.now()
    retrieving_archive.retrieval_task_id = retrieval_job_id

    # WHEN invoking update_job_statuses
    with mock.patch.object(
        AuthToken,
        "model_validate",
        return_value=test_auth_token,
    ), mock.patch.object(
        APIRequest,
        "api_request_from_content",
        return_value=ok_miria_response,
    ), mock.patch.object(
        GetJobStatusPayload,
        "get_job_status",
        return_value=GetJobStatusResponse(id=retrieval_job_id, status=job_status),
    ):
        result = cli_runner.invoke(
            update_job_statuses,
            obj=archive_context,
        )

    # THEN the command should have exited successfully and updated the archive record
    assert result.exit_code == 0
    if job_status == JobStatus.COMPLETED:
        assert archive_context.housekeeper_api.get_archive_entries(
            retrieval_task_id=retrieval_job_id
        )[0].retrieved_at
    elif job_status in FAILED_JOB_STATUSES:
        assert not archive_context.housekeeper_api.get_archive_entries(
            retrieval_task_id=retrieval_job_id
        )
    elif job_status in ONGOING_JOB_STATUSES:
        assert not archive_context.housekeeper_api.get_archive_entries(
            retrieval_task_id=retrieval_job_id
        )[0].retrieved_at
