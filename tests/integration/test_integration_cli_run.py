from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from subprocess import CompletedProcess
from typing import cast
from unittest.mock import ANY, Mock, create_autospec

import pytest
from click.testing import CliRunner, Result
from housekeeper.store import database as hk_database
from housekeeper.store.models import Bundle, Version
from housekeeper.store.store import Store as HousekeeperStore
from pytest import TempPathFactory
from pytest_httpserver import HTTPServer

from cg.apps.tb.api import IDTokenCredentials
from cg.cli.base import base
from cg.cli.workflow.microsalt.base import run
from cg.constants.constants import Workflow
from cg.constants.gene_panel import GenePanelMasterList
from cg.constants.process import EXIT_SUCCESS
from cg.store import database as cg_database
from cg.store.models import Case, IlluminaFlowCell, IlluminaSequencingRun, Sample
from cg.store.store import Store
from cg.utils import commands
from tests.store_helpers import StoreHelpers


@pytest.fixture(autouse=True)
def valid_google_token(mocker):
    mocker.patch.object(
        IDTokenCredentials,
        "from_service_account_file",
        return_value=create_autospec(IDTokenCredentials, token="some token"),
    )


@pytest.fixture(scope="session")
def httpserver_listen_address():
    return ("localhost", 8888)


@pytest.fixture
def store() -> Generator[Store, None, None]:
    # TODO: use uri from config file
    cg_database.initialize_database("sqlite:///file:cg?mode=memory&cache=shared&uri=true")
    cg_database.create_all_tables()
    store = Store()
    yield store
    cg_database.drop_all_tables()


@pytest.fixture
def status_db(store: Store) -> Generator[Store, None, None]:
    yield store


@pytest.fixture
def housekeeper_db() -> Generator[HousekeeperStore, None, None]:
    # TODO: use uri from config file
    hk_database.initialize_database("sqlite:///file:housekeeper?mode=memory&cache=shared&uri=true")
    hk_database.create_all_tables()
    store = HousekeeperStore(root="/housekeeper/root")
    yield store
    hk_database.drop_all_tables()


@pytest.mark.integration
def test_start_available_mip_dna(
    status_db: Store,
    housekeeper_db: HousekeeperStore,
    helpers: StoreHelpers,
    tmp_path_factory: TempPathFactory,
    mocker,
    httpserver: HTTPServer,
):
    cli_runner = CliRunner()

    case: Case = helpers.add_case(store=status_db, data_analysis=Workflow.MIP_DNA)
    sample: Sample = helpers.add_sample(store=status_db, last_sequenced_at=datetime.now())
    helpers.relate_samples(base_store=status_db, case=case, samples=[sample])

    flow_cell: IlluminaFlowCell = helpers.add_illumina_flow_cell(store=status_db)
    sequencing_run: IlluminaSequencingRun = helpers.add_illumina_sequencing_run(
        store=status_db, flow_cell=flow_cell
    )
    helpers.add_illumina_sample_sequencing_metrics_object(
        store=status_db, sample_id=sample.internal_id, sequencing_run=sequencing_run, lane=1
    )

    bed_files_path: Path = tmp_path_factory.mktemp("bed_files")
    delivery_report_path: Path = tmp_path_factory.mktemp("delivery_report")
    bundle_data = {
        "name": sample.internal_id,
        "created": datetime.now(),
        "expires": datetime.now(),
        "files": [
            {
                "path": bed_files_path.as_posix(),
                "archive": False,
                "tags": ["bed", sample.id, "coverage"],
            },
            {
                "path": delivery_report_path.as_posix(),
                "archive": False,
                "tags": ["delivery-report"],
            },
        ],
    }

    bundle, version = cast(tuple[Bundle, Version], housekeeper_db.add_bundle(bundle_data))
    housekeeper_db.session.add(bundle)
    housekeeper_db.session.add(version)
    housekeeper_db.session.commit()

    subprocess_mock = mocker.patch.object(commands, "subprocess")
    subprocess_mock.run = Mock(
        return_value=create_autospec(
            CompletedProcess, returncode=EXIT_SUCCESS, stdout=b"", stderr=b""
        )
    )

    httpserver.expect_request(f"/lims/api/v2/samples/{sample.internal_id}").respond_with_json(
        {"what": "?"}
    )

    # WHEN running start available
    result: Result = cli_runner.invoke(
        base,
        [
            "--config",
            "tests/integration/config/cg-test.yaml",
            "workflow",
            "mip-dna",
            "start-available",
        ],
    )

    subprocess_mock.run.assert_called_once_with(
        [
            "tests/integration/config/scout/binary",
            "--config",
            "tests/integration/config/scout/config",
            "export",
            "panel",
            "--bed",
            ANY,
            ANY,
            ANY,
            "--build",
            "37",
        ],
        check=False,
        stdout=ANY,
        stderr=ANY,
    )

    # The order of the bed arguments is not deterministic, so we need to look at them as a set
    bed_args = subprocess_mock.run.call_args.args[0][6:9]
    assert set(bed_args) == {
        GenePanelMasterList.OMIM_AUTO,
        GenePanelMasterList.PANELAPP_GREEN,
        "panel_test",
    }

    assert result.exit_code == 0
    updated_case = status_db.get_case_by_internal_id(case.internal_id)
    assert cast(Case, updated_case).action == "running"
