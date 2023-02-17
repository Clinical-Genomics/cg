"""Test CG CLI upload module."""
import logging
from datetime import datetime, timedelta

from cgmodels.cg.constants import Pipeline
from cg.cli.upload.base import upload
from cg.constants.process import EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cg.store import Store, models
from click.testing import CliRunner
from tests.cli.workflow.conftest import tb_api
from tests.store_helpers import StoreHelpers


def test_upload_started_long_time_ago_raises_exception(
    cli_runner: CliRunner,
    base_context: CGConfig,
    helpers: StoreHelpers,
):
    """Test that an upload for a missing case does fail hard."""

    # GIVEN an analysis that is already uploading since a week ago
    disk_store: Store = base_context.status_db
    case = helpers.add_case(disk_store)
    case_id = case.internal_id
    today = datetime.now()
    upload_started = today - timedelta(hours=100)
    helpers.add_analysis(disk_store, case=case, uploading=True, upload_started=upload_started)

    # WHEN trying to upload an analysis that was started a long time ago
    result = cli_runner.invoke(upload, ["-f", case_id], obj=base_context)

    # THEN an exception should have be thrown
    assert result.exit_code != 0
    assert result.exception


def test_upload_force_restart(cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers):
    """Test that a case that is already uploading can be force restarted."""

    # GIVEN an analysis that is already uploading
    disk_store: Store = base_context.status_db
    case: models.Family = helpers.add_case(disk_store)
    case_id: str = case.internal_id

    helpers.add_analysis(disk_store, case=case, uploading=True)

    # WHEN trying to upload it again with the force restart flag
    result = cli_runner.invoke(upload, ["-f", case_id, "-r"], obj=base_context)

    # THEN it tries to restart the upload
    assert "already started" not in result.output


def test_upload_mip_rna(
    caplog,
    cli_runner: CliRunner,
    base_context: CGConfig,
    helpers: StoreHelpers,
):
    """Tests that a Mip RNA case uploads successfully"""
    caplog.set_level(logging.INFO)

    # GIVEN an un-uploaded Mip RNA case
    disk_store: Store = base_context.status_db
    case: models.Family = helpers.add_case(disk_store, data_analysis=Pipeline.MIP_RNA)
    case_id: str = case.internal_id
    helpers.add_sample(disk_store, is_rna=True)
    helpers.add_analysis(disk_store, pipeline=Pipeline.MIP_RNA, case=case, uploading=False)
    # helpers.add_case_with_sample(disk_store, case_id=case_id)  # , sample_id=sample.internal_id)

    # WHEN uploading
    result = cli_runner.invoke(upload, ["-f", case_id], obj=base_context)

    # THEN exits successfully and states that the upload was successful in the log
    # assert result.exit_code == EXIT_SUCCESS
    assert f"Upload of case {case_id} was successful" in caplog.text


def test_upload_mip_dna(
    caplog,
    cli_runner: CliRunner,
    base_context: CGConfig,
    helpers: StoreHelpers,
):
    """Tests that a Mip DNA case uploads successfully"""

    caplog.set_level(logging.INFO)

    # GIVEN an un-uploaded Mip DNA case
    disk_store: Store = base_context.status_db
    case: models.Family = helpers.add_case(
        disk_store,
        data_analysis=Pipeline.MIP_DNA,
    )
    case_id: str = case.internal_id
    sample = helpers.add_sample(disk_store, is_rna=False)
    sample_id: str = sample.internal_id
    helpers.add_analysis(disk_store, case=case, pipeline=Pipeline.MIP_DNA, uploading=False)
    helpers.add_relationship(disk_store, sample=sample, case=case)
    # helpers.add_case_with_sample(disk_store, case_id=case_id, sample_id=sample_id)

    # WHEN
    result = cli_runner.invoke(upload, ["-f", case_id], obj=base_context)

    # THEN exits successfully and states that the upload was successful in the log
    assert result.exit_code == EXIT_SUCCESS
    assert f"Upload of case {case_id} was successful" in caplog.text


def test_upload_mip_dna_with_context(
    caplog, cli_runner: CliRunner, helpers: StoreHelpers, mip_dna_context: CGConfig
):
    """Tests that a Mip DNA case uploads successfully"""

    caplog.set_level(logging.INFO)

    # GIVEN an un-uploaded Mip DNA case
    disk_store: Store = mip_dna_context.status_db
    case: models.Family = helpers.add_case(
        disk_store,
        data_analysis=Pipeline.MIP_DNA,
    )
    case_id: str = case.internal_id

    helpers.add_analysis(disk_store, case=case, pipeline=Pipeline.MIP_DNA, uploading=False)

    # WHEN
    result = cli_runner.invoke(upload, ["-f", case_id], obj=mip_dna_context)

    # THEN exits successfully and states that the upload was successful in the log
    assert result.exit_code == EXIT_SUCCESS
    assert f"Upload of case {case_id} was successful" in caplog.text


def test_upload_balsamic(
    caplog,
    cli_runner: CliRunner,
    base_context: CGConfig,
    helpers: StoreHelpers,
):
    """Tests that a BALSAMIC case uploads successfully"""

    caplog.set_level(logging.INFO)

    # GIVEN an un-uploaded BALSAMIC case
    disk_store: Store = base_context.status_db
    case: models.Family = helpers.add_case(
        disk_store,
        data_analysis=Pipeline.BALSAMIC,
    )
    case_id: str = case.internal_id

    helpers.add_analysis(disk_store, case=case, uploading=False)

    # WHEN
    result = cli_runner.invoke(upload, ["-f", case_id], obj=base_context)

    # THEN exits successfully and states that the upload was successful in the log
    assert result.exit_code == EXIT_SUCCESS
    assert f"Upload of case {case_id} was successful" in caplog.text
