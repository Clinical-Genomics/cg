from collections.abc import Callable
from datetime import datetime as dt
from pathlib import Path
from typing import cast
from unittest.mock import Mock

import pytest
from click.testing import CliRunner, Result
from housekeeper.store.models import Bundle, Version
from housekeeper.store.store import Store as HousekeeperStore
from pytest_mock import MockerFixture

from cg.cli.base import base
from cg.constants.constants import DataDelivery, Workflow
from cg.store.store import Store
from cg.utils import commands
from tests.integration.utils import IntegrationTestPaths, copy_integration_test_file
from tests.store_helpers import StoreHelpers


@pytest.fixture(autouse=True)
def mocked_commands_and_outputs() -> dict[str, bytes]:
    return {
        "/scout_38/binary --config /scout_38/config export cases --json --case-id": b"",
    }


@pytest.mark.xdist_group(name="integration")
@pytest.mark.integration
def test_upload_raredisease_to_scout(
    status_db: Store,
    helpers: StoreHelpers,
    housekeeper_db: HousekeeperStore,
    test_run_paths: IntegrationTestPaths,
    mock_run_commands: Callable,
    mocker: MockerFixture,
):
    cli_runner = CliRunner()

    # GIVEN a config file with valid database URIs and directories
    config_path: Path = test_run_paths.cg_config_file
    test_root_dir: Path = test_run_paths.test_root_dir

    # GIVEN a raredisease case
    case = helpers.add_case(
        store=status_db, data_analysis=Workflow.RAREDISEASE, data_delivery=DataDelivery.SCOUT
    )

    # GIVEN a completed raredisease analysis of that case and a run directory
    helpers.add_analysis(
        store=status_db,
        case=case,
        workflow=Workflow.RAREDISEASE,
        data_delivery=DataDelivery.SCOUT,
        completed_at=dt.now(),
    )
    Path(test_root_dir, "raredisease_root_path", case.internal_id).mkdir(parents=True)

    files = []
    for tag_set in [
        ["delivery-report"],
        ["multiqc-html"],
        ["ped-check", "peddy"],
        ["peddy", "ped"],
        ["peddy", "sex-check"],
        ["smn-calling"],
        ["vcf", "mobile-elements", "clinical"],
        ["vcf", "mobile-elements", "research"],
        ["vcf-snv-research"],
        ["vcf-snv-clinical"],
        ["mitochondria", "vcf-sv-research"],
        ["mitochondria", "vcf-sv-clinical"],
        ["vcf-sv-research"],
        ["vcf-str"],
    ]:
        path = Path(test_root_dir, "-".join(tag_set))
        path.touch()
        files.append({"path": path.as_posix(), "archive": False, "tags": tag_set})

    manifest_path = Path(test_root_dir, "manifest.json")
    copy_integration_test_file(
        from_path=Path("tests/fixtures/analysis/raredisease/manifest.json"), to_path=manifest_path
    )

    files.append({"path": manifest_path.as_posix(), "archive": False, "tags": ["manifest"]})

    # GIVEN a housekeeper bundle for that analysis
    bundle, _version = bundle, version = cast(
        tuple[Bundle, Version],
        housekeeper_db.add_bundle(
            data={
                "name": case.internal_id,
                "created": dt.now(),
                "expires": dt.now(),
                "files": files,
            }
        ),
    )
    # housekeeper_db.add_file()
    housekeeper_db.session.add(bundle)
    housekeeper_db.session.commit()

    subprocess_mock = mocker.patch.object(commands, "subprocess")
    subprocess_mock.run = Mock(side_effect=mock_run_commands)

    # WHEN running post-process all
    result: Result = cli_runner.invoke(
        base,
        ["--config", config_path.as_posix(), "upload", "scout", case.internal_id],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    subprocess_mock.run.assert_called_with("/scout_38/binary")
