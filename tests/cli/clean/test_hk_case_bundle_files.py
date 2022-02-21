import logging
import datetime as dt

from cgmodels.cg.constants import Pipeline

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.models.cg_config import CGConfig
from click.testing import CliRunner
from tests.store_helpers import StoreHelpers

from cg.cli.clean import hk_case_bundle_files, PIPELINE_PROTECTED_TAGS

from cg.store import Store

from cg.store import models
from housekeeper.store import models as hk_models


def test_date_days_ago_zero_days():
    # GIVEN

    # WHEN calculating days ago 0 days ago
    result: dt.datetime = get_date_days_ago(0)

    # THEN result should be equal to today
    assert isinstance(result, dt.datetime)
    assert result.date() == dt.datetime.now().date()


def test_date_days_ago_one_days():
    # GIVEN we know what date it was yesterday
    days_ago = 1
    yesterday = dt.datetime.now() - dt.timedelta(days=days_ago)

    # WHEN calculating days ago 1 days ago
    result: dt.datetime = get_date_days_ago(days_ago)

    # THEN result should be equal to yesterday
    assert isinstance(result, dt.datetime)
    assert result.date() == yesterday.date()


def get_date_days_ago(days_ago: int) -> dt.datetime:
    return dt.datetime.now() - dt.timedelta(days=days_ago)


def test_clean_hk_case_files_too_old(cli_runner: CliRunner, clean_context: CGConfig, caplog):
    # GIVEN no analysis in database
    days_ago = 365 * 100
    date_one_year_ago = get_date_days_ago(days_ago)
    context = clean_context
    assert not context.status_db.get_analyses_before_date(before=date_one_year_ago).all()

    # WHEN running the clean command
    caplog.set_level(logging.DEBUG)
    result = cli_runner.invoke(
        hk_case_bundle_files, ["--days-old", days_ago, "--dry-run"], obj=context, catch_exceptions=False
    )

    # THEN it should be successful
    assert result.exit_code == 0
    # THEN it should report not having cleaned anything
    assert f"Process freed 0.0 GB" in caplog.text


def test_clean_hk_case_files_single_analysis(
        caplog,
        cli_runner: CliRunner,
        cg_context: CGConfig,
        helpers: StoreHelpers,
        timestamp: dt.datetime,
):
    # GIVEN we have some analyses to clean
    context: CGConfig = cg_context
    store: Store = context.status_db
    days_ago: int = 1
    date_days_ago: dt.datetime = get_date_days_ago(days_ago)
    pipeline: Pipeline = Pipeline.MIP_DNA

    analysis: models.Analysis = helpers.add_analysis(store=store, started_at=date_days_ago, completed_at=date_days_ago,
                                                     pipeline=pipeline)
    bundle_name: str = analysis.family.internal_id

    # GIVEN a housekeeper api with some alignment files
    file_path = "path/to_file.cram"
    hk_bundle_data = {
        "name": bundle_name,
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {"path": file_path, "archive": False, "tags": [bundle_name, "cram"]},
        ],
    }
    helpers.ensure_hk_bundle(cg_context.housekeeper_api, bundle_data=hk_bundle_data)

    # WHEN running the clean command
    caplog.set_level(logging.DEBUG)
    result = cli_runner.invoke(
        hk_case_bundle_files, ["--days-old", days_ago, "--dry-run"], obj=context
    )

    # THEN it should be successful
    assert result.exit_code == 0
    # THEN it should report some files to clean
    assert "Cleaning analysis" in caplog.text
    assert "Version found for" in caplog.text
    assert "has the tags" in caplog.text
    assert "has no protected tags" in caplog.text
    assert "not on disk" in caplog.text


def test_clean_hk_case_files_analysis_with_protected_tag(
        caplog,
        cli_runner: CliRunner,
        cg_context: CGConfig,
        helpers: StoreHelpers,
        timestamp: dt.datetime,
):
    # GIVEN we have some analyses to clean
    context: CGConfig = cg_context
    store: Store = context.status_db
    days_ago: int = 1
    date_days_ago: dt.datetime = get_date_days_ago(days_ago)
    pipeline: Pipeline = Pipeline.MIP_DNA

    analysis: models.Analysis = helpers.add_analysis(store=store, started_at=date_days_ago, completed_at=date_days_ago,
                                                     pipeline=pipeline)
    bundle_name: str = analysis.family.internal_id

    # GIVEN a housekeeper api with some alignment files with protected tags
    protected_tags = PIPELINE_PROTECTED_TAGS[pipeline][0]
    file_path = "path/to_file.fastq"
    hk_bundle_data = {
        "name": bundle_name,
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {"path": file_path, "archive": False, "tags": protected_tags},
        ],
    }
    print(f"{hk_bundle_data=}")
    helpers.ensure_hk_bundle(cg_context.housekeeper_api, bundle_data=hk_bundle_data)

    # WHEN running the clean command
    caplog.set_level(logging.DEBUG)
    result = cli_runner.invoke(
        hk_case_bundle_files, ["--days-old", days_ago, "--dry-run"], obj=context, catch_exceptions=False
    )

    # THEN it should be successful
    assert result.exit_code == 0
    # THEN it should report some files to clean
    assert "Cleaning analysis" in caplog.text
    assert "Version found for" in caplog.text
    assert "has the tags" in caplog.text
    assert "has the protected tag(s)" in caplog.text
