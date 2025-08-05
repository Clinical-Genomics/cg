import shutil
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from subprocess import CompletedProcess
from time import sleep
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
from cg.cli.workflow.mip import base as mip_base
from cg.constants.constants import CaseActions, Workflow
from cg.constants.gene_panel import GenePanelMasterList
from cg.constants.process import EXIT_SUCCESS
from cg.constants.tb import AnalysisType
from cg.store import database as cg_database
from cg.store.models import Case, IlluminaFlowCell, IlluminaSequencingRun, Order, Sample
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
def status_db_uri() -> str:
    return "sqlite:///file:cg?mode=memory&cache=shared&uri=true"


@pytest.fixture
def housekeeper_db_uri() -> str:
    return "sqlite:///file:housekeeper?mode=memory&cache=shared&uri=true"


@pytest.fixture
def store(status_db_uri: str) -> Generator[Store, None, None]:
    cg_database.initialize_database(status_db_uri)
    cg_database.create_all_tables()
    store = Store()
    yield store
    cg_database.drop_all_tables()


@pytest.fixture
def status_db(store: Store) -> Generator[Store, None, None]:
    yield store


@pytest.fixture
def housekeeper_db(
    housekeeper_db_uri: str, tmp_path_factory: TempPathFactory
) -> Generator[HousekeeperStore, None, None]:
    hk_database.initialize_database(housekeeper_db_uri)
    hk_database.create_all_tables()
    housekeeper_root: Path = tmp_path_factory.mktemp("housekeeper")
    store = HousekeeperStore(root=housekeeper_root.as_posix())
    yield store
    hk_database.drop_all_tables()


@pytest.mark.integration
def test_start_available_mip_dna(
    status_db: Store,
    status_db_uri: str,
    housekeeper_db_uri: str,
    housekeeper_db: HousekeeperStore,
    helpers: StoreHelpers,
    tmp_path_factory: TempPathFactory,
    mocker,
    httpserver: HTTPServer,
):
    """Test a successful run of the command start-available mip-dna with one case to be analysed"""
    cli_runner = CliRunner()

    # GIVEN a mip root directory
    test_root_dir = tmp_path_factory.mktemp("test_start_available_mip_dna")
    # GIVEN a config file with valid database uris and directories
    config_path = create_config(status_db_uri, housekeeper_db_uri, test_root_dir)

    # GIVEN a case with existing qc files
    ticket_id = 12345
    case: Case = helpers.add_case(
        store=status_db, data_analysis=Workflow.MIP_DNA, ticket=str(ticket_id)
    )
    create_qc_file(test_root_dir, case)

    # GIVEN an order associated with the case
    order: Order = helpers.add_order(
        store=status_db, ticket_id=ticket_id, customer_id=case.customer_id
    )
    status_db.link_case_to_order(order_id=order.id, case_id=case.id)

    # GIVEN a sample associated with the case
    sample: Sample = helpers.add_sample(
        store=status_db, last_sequenced_at=datetime.now(), application_type=AnalysisType.WGS
    )
    helpers.relate_samples(base_store=status_db, case=case, samples=[sample])

    # GIVEN a flow cell and sequencing run associated with the sample
    flow_cell: IlluminaFlowCell = helpers.add_illumina_flow_cell(store=status_db)
    sequencing_run: IlluminaSequencingRun = helpers.add_illumina_sequencing_run(
        store=status_db, flow_cell=flow_cell
    )
    helpers.add_illumina_sample_sequencing_metrics_object(
        store=status_db, sample_id=sample.internal_id, sequencing_run=sequencing_run, lane=1
    )

    # GIVEN sample bundle data directories exists
    bed_files_path: Path = tmp_path_factory.mktemp("bed_files")
    delivery_report_path: Path = tmp_path_factory.mktemp("delivery_report")

    # GIVEN the bundle data exists in Housekeeper
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

    # GIVEN the scout command returns exported panel data
    subprocess_mock = mocker.patch.object(commands, "subprocess")

    def mock_run(*args, **kwargs):
        command = args[0]

        stdout = b""

        if ("export" in command) and ("panel" in command):
            stdout += b"22\t26995242\t27014052\t2397\tCRYBB1\n22\t38452318\t38471708\t9394\tPICK1\n"
        return create_autospec(CompletedProcess, returncode=EXIT_SUCCESS, stdout=stdout, stderr=b"")

    subprocess_mock.run = Mock(side_effect=mock_run)

    # GIVEN an email adress can be determined from the environment
    mocker.patch.object(mip_base, "environ_email", return_value="testuser@scilifelab.se")

    # GIVEN the trailblazer API returns an uncompleted analysis
    httpserver.expect_request(
        "/trailblazer/get-latest-analysis", data='{"case_id": "' + case.internal_id + '"}'
    ).respond_with_json(
        {
            "id": "1",
            "logged_at": "",
            "started_at": "",
            "completed_at": "",
            "out_dir": "out/dir",
            "config_path": "config/path",
        }
    )

    # GIVEN a pending analysis can be added to the Trailblazer API
    httpserver.expect_request(
        "/trailblazer/add-pending-analysis",
        data=b'{"case_id": "%(case_id)s", "email": "linnealofdahl@scilifelab.se", "type": "wgs", "config_path": "%(test_root_dir)s/mip-dna/cases/%(case_id)s/analysis/slurm_job_ids.yaml", "order_id": 1, "out_dir": "%(test_root_dir)s/mip-dna/cases/%(case_id)s/analysis", "priority": "normal", "workflow": "MIP-DNA", "ticket": "%(ticket_id)s", "workflow_manager": "slurm", "tower_workflow_id": null, "is_hidden": true}'
        % {
            b"case_id": case.internal_id.encode(),
            b"ticket_id": str(ticket_id).encode(),
            b"test_root_dir": str(test_root_dir).encode(),
        },
    ).respond_with_json(
        {
            "id": "1",
            "logged_at": "",
            "started_at": "",
            "completed_at": "",
            "out_dir": "out/dir",
            "config_path": "config/path",
        }
    )

    # WHEN running mip-dna start-available
    result: Result = cli_runner.invoke(
        base,
        [
            "--config",
            config_path.as_posix(),
            "workflow",
            "mip-dna",
            "start-available",
        ],
    )

    # THEN a scout command is called to export panel beds
    subprocess_mock.run.assert_any_call(
        [
            f"{test_root_dir}/scout/binary",
            "--config",
            f"{test_root_dir}/scout/config",
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
    bed_args = subprocess_mock.run.call_args_list[0][0][0][6:9]
    assert set(bed_args) == {
        GenePanelMasterList.OMIM_AUTO,
        GenePanelMasterList.PANELAPP_GREEN,
        "panel_test",
    }

    # THEN a scout command is called to export managed variants
    subprocess_mock.run.assert_any_call(
        [
            f"{test_root_dir}/scout/binary",
            "--config",
            f"{test_root_dir}/scout/config",
            "export",
            "managed",
            "--build",
            "37",
        ],
        check=False,
        stdout=ANY,
        stderr=ANY,
    )

    # THEN a mip-dna analysis is started with the expected parameters
    subprocess_mock.run.assert_any_call(
        f"""{test_root_dir}/mip-dna/conda_bin run --name S_mip12.1 {test_root_dir}/mip-dna/bin analyse rd_dna --config {test_root_dir}/mip-dna/config/mip12.1-dna-stage.yaml {case.internal_id} --slurm_quality_of_service normal --email testuser@scilifelab.se""",
        check=False,
        shell=True,
        stdout=ANY,
        stderr=ANY,
    )

    # THEN a successful exit code is returned
    assert result.exit_code == 0

    # THEN an analysis has been created for the case
    assert len(case.analyses) == 1

    # THEN the case action is set to running
    status_db.session.refresh(case)
    assert case.action == CaseActions.RUNNING

    # THEN gene_panels and managed_variant files has been created
    case_dir = Path(test_root_dir, "mip-dna", "cases", case.internal_id)
    assert Path(case_dir, "gene_panels.bed").exists()
    assert Path(case_dir, "managed_variants.vcf").exists()


def create_qc_file(test_root_dir, case) -> Path:
    filepath = Path(
        f"{test_root_dir}/mip-dna/cases/{case.internal_id}/analysis/{case.internal_id}_qc_sample_info.yaml"
    )
    filepath.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2("tests/fixtures/apps/mip/dna/store/case_qc_sample_info.yaml", filepath)
    return filepath


def create_config(status_db_uri, housekeeper_db_uri, test_root_dir):
    template_path = "tests/integration/config/cg-test.yaml"
    with open(template_path) as f:
        config_content = f.read()

    config_content = config_content.format(
        test_root_dir=test_root_dir,
        status_db_uri=status_db_uri,
        housekeeper_db_uri=housekeeper_db_uri,
    )

    config_path = Path(test_root_dir, "cg-config.yaml")
    with open(config_path, "w") as f:
        f.write(config_content)
    return config_path
