import logging
from datetime import datetime

from cg.cli.clean import hk_alignment_files
from cg.models.cg_config import CGConfig
from click.testing import CliRunner
from tests.store_helpers import StoreHelpers


def test_clean_hk_alignment_files_no_files(cli_runner: CliRunner, cg_context: CGConfig, caplog):
    # GIVEN a housekeeper api and a bundle without files
    bundle_name = "non_existing"
    assert not cg_context.housekeeper_api.bundle(bundle_name)

    # WHEN running the clean hk alignment files command
    caplog.set_level(logging.INFO)
    result = cli_runner.invoke(hk_alignment_files, [bundle_name], obj=cg_context)

    # THEN assert it exits with success
    assert result.exit_code == 0
    # THEN assert it was communicated that no files where found
    assert f"Could not find any files ready for cleaning for bundle {bundle_name}" in caplog.text


def test_clean_hk_alignment_files_dry_run(
    cli_runner: CliRunner,
    cg_context: CGConfig,
    helpers: StoreHelpers,
    case_id: str,
    timestamp: datetime,
    caplog,
):
    # GIVEN a housekeeper api with some alignment files
    file_path = "path/to_file.cram"
    hk_bundle_data = {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {"path": file_path, "archive": False, "tags": [case_id, "cram"]},
        ],
    }
    helpers.ensure_hk_bundle(cg_context.housekeeper_api, bundle_data=hk_bundle_data)

    # WHEN running the clean command in dry run mode
    caplog.set_level(logging.INFO)
    result = cli_runner.invoke(hk_alignment_files, [case_id, "--yes", "--dry-run"], obj=cg_context)

    # THEN assert it exits with success
    assert result.exit_code == 0
    # THEN assert that the files where removed
    assert f"Deleting {file_path} from database" in caplog.text
