import datetime as dt
import logging

from cg.cli.clean import hk_case_bundle_files
from cg.constants.housekeeper_tags import WORKFLOW_PROTECTED_TAGS
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Analysis
from cgmodels.cg.constants import Pipeline
from click.testing import CliRunner
from cg.utils.date import get_date_days_ago

from tests.store_helpers import StoreHelpers


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


def test_clean_hk_case_files_too_old(cli_runner: CliRunner, clean_context: CGConfig, caplog):
    # GIVEN no analysis in database
    days_ago = 365 * 100
    date_one_year_ago = get_date_days_ago(days_ago)
    context = clean_context
    assert not context.status_db.get_analyses_started_at_before(started_at_before=date_one_year_ago)

    # WHEN running the clean command
    caplog.set_level(logging.DEBUG)
    result = cli_runner.invoke(
        hk_case_bundle_files,
        ["--days-old", days_ago, "--dry-run"],
        obj=context,
        catch_exceptions=False,
    )

    # THEN it should be successful
    assert result.exit_code == 0
    # THEN it should report not having cleaned anything
    assert f"Process freed 0.0 GB" in caplog.text


def test_clean_hk_case_files_single_analysis(
    caplog,
    cg_context: CGConfig,
    cli_runner: CliRunner,
    helpers: StoreHelpers,
    hk_bundle_data: dict,
    timestamp: dt.datetime,
):
    # GIVEN we have some analyses to clean
    context: CGConfig = cg_context
    store: Store = context.status_db
    days_ago: int = 1
    date_days_ago: dt.datetime = get_date_days_ago(days_ago)
    pipeline: Pipeline = Pipeline.MIP_DNA

    analysis: Analysis = helpers.add_analysis(
        store=store, started_at=date_days_ago, completed_at=date_days_ago, pipeline=pipeline
    )
    bundle_name: str = analysis.family.internal_id

    # GIVEN a housekeeper api with some files
    hk_bundle_data["name"] = bundle_name
    helpers.ensure_hk_bundle(cg_context.housekeeper_api, bundle_data=hk_bundle_data)

    # WHEN running the clean command
    caplog.set_level(logging.DEBUG)
    result = cli_runner.invoke(
        hk_case_bundle_files, ["--days-old", days_ago, "--dry-run"], obj=context
    )

    # THEN it should be successful
    assert result.exit_code == 0
    # THEN it should report some files to clean
    assert "Version found for" in caplog.text
    assert "has the tags" in caplog.text
    assert "has no protected tags" in caplog.text
    assert "found on disk" in caplog.text


def test_clean_hk_case_files_analysis_with_protected_tag(
    caplog,
    cg_context: CGConfig,
    cli_runner: CliRunner,
    helpers: StoreHelpers,
    hk_bundle_data: dict,
    timestamp: dt.datetime,
):
    # GIVEN we have some analyses to clean
    context: CGConfig = cg_context
    store: Store = context.status_db
    days_ago: int = 1
    date_days_ago: dt.datetime = get_date_days_ago(days_ago)
    pipeline: Pipeline = Pipeline.MIP_DNA

    analysis: Analysis = helpers.add_analysis(
        store=store, started_at=date_days_ago, completed_at=date_days_ago, pipeline=pipeline
    )
    bundle_name: str = analysis.family.internal_id

    # GIVEN a housekeeper api with some file with protected tags
    protected_tags = WORKFLOW_PROTECTED_TAGS[pipeline][0]
    hk_bundle_data["name"] = bundle_name
    hk_bundle_data["files"][0]["tags"] = protected_tags
    helpers.ensure_hk_bundle(cg_context.housekeeper_api, bundle_data=hk_bundle_data)

    # WHEN running the clean command
    caplog.set_level(logging.DEBUG)
    result = cli_runner.invoke(
        hk_case_bundle_files,
        ["--days-old", days_ago, "--dry-run"],
        obj=context,
        catch_exceptions=False,
    )

    # THEN it should be successful
    assert result.exit_code == 0
    # THEN it should report some files to clean
    assert "Version found for" in caplog.text
    assert "has the tags" in caplog.text
    assert "has the protected tag(s)" in caplog.text
