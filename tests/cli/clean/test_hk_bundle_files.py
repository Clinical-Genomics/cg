import logging
from datetime import datetime

from click.testing import CliRunner

from cg.cli.clean import hk_bundle_files
from cg.models.cg_config import CGConfig
from tests.store_helpers import StoreHelpers


def test_clean_hk_bundle_files_no_files(cli_runner: CliRunner, cg_context: CGConfig, caplog):
    # GIVEN a housekeeper api and a bundle without files
    bundle_name = "non_existing"
    assert not cg_context.housekeeper_api.bundle(bundle_name)
    cg_context.status_db.get_case_by_internal_id(bundle_name)

    # WHEN running the clean hk alignment files command
    caplog.set_level(logging.INFO)
    result = cli_runner.invoke(
        hk_bundle_files, ["-c", bundle_name, "--tags", "tag"], obj=cg_context
    )

    # THEN assert it exits with success
    assert result.exit_code == 0
    # THEN assert it was communicated that no files where found
    assert "Process freed 0.0GB. Dry run: False" in caplog.text


def test_clean_hk_bundle_files_dry_run(
    caplog,
    case_id: str,
    cg_context: CGConfig,
    cli_runner: CliRunner,
    helpers: StoreHelpers,
    timestamp: datetime,
):
    # GIVEN a housekeeper api with some alignment files
    file_path = "path/to_file.cram"
    tag = "cram"
    hk_bundle_data = {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {"path": file_path, "archive": False, "tags": [case_id, tag]},
        ],
    }
    store = cg_context.status_db
    case = helpers.ensure_case(store=store, case_id=case_id)
    helpers.add_analysis(store=store, case=case, started_at=timestamp, completed_at=timestamp)
    helpers.ensure_hk_bundle(cg_context.housekeeper_api, bundle_data=hk_bundle_data)

    # WHEN running the clean command in dry run mode
    caplog.set_level(logging.INFO)
    result = cli_runner.invoke(
        hk_bundle_files, ["-c", case_id, "--dry-run", "--tags", tag], obj=cg_context
    )

    # THEN assert it exits with success
    assert result.exit_code == 0
    # THEN assert that the files where removed
    assert f"{file_path} not on disk" in caplog.text
