import shutil
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
from pytest_mock import MockerFixture

from cg.apps.tb.api import IDTokenCredentials
from cg.cli.base import base
from cg.cli.workflow.mip import base as mip_base
from cg.constants.constants import CaseActions, Workflow
from cg.constants.gene_panel import GenePanelMasterList
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.constants.process import EXIT_SUCCESS
from cg.constants.tb import AnalysisType
from cg.meta.workflow import analysis
from cg.services.analysis_starter.configurator.implementations import (
    mip_dna as mip_dna_configurator,
)
from cg.services.analysis_starter.submitters.subprocess import submitter
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
def httpserver_listen_address() -> tuple[str, int]:
    return ("localhost", 8888)


@pytest.fixture
def status_db_uri() -> str:
    return "sqlite:///file:cg?mode=memory&cache=shared&uri=true"


@pytest.fixture
def housekeeper_db_uri() -> str:
    return "sqlite:///file:housekeeper?mode=memory&cache=shared&uri=true"


@pytest.fixture
def status_db(status_db_uri: str) -> Generator[Store, None, None]:
    cg_database.initialize_database(status_db_uri)
    cg_database.create_all_tables()
    store = Store()
    yield store
    cg_database.drop_all_tables()


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


@pytest.fixture
def scout_export_panel_stdout() -> bytes:
    return b"22\t26995242\t27014052\t2397\tCRYBB1\n22\t38452318\t38471708\t9394\tPICK1\n"


@pytest.mark.parametrize(
    "test_command",
    ["start-available", "dev-start-available"],
)
@pytest.mark.integration
def test_start_available_mip_dna(
    test_command: str,
    helpers: StoreHelpers,
    housekeeper_db_uri: str,
    housekeeper_db: HousekeeperStore,
    httpserver: HTTPServer,
    mocker: MockerFixture,
    scout_export_panel_stdout: bytes,
    status_db_uri: str,
    status_db: Store,
    tmp_path_factory: TempPathFactory,
):
    """Test a successful run of the command 'cg workflow mip-dna start-available'
    with one case to be analysed that has not been analysed before."""
    cli_runner = CliRunner()

    # GIVEN a MIP-DNA root directory
    test_root_dir: Path = tmp_path_factory.mktemp("test_start_available_mip_dna")
    # GIVEN a config file with valid database URIs and directories
    config_path: Path = create_parsed_config(
        status_db_uri=status_db_uri,
        housekeeper_db_uri=housekeeper_db_uri,
        test_root_dir=test_root_dir.as_posix(),
    )
    mip_dna_path = Path(test_root_dir, "mip-dna")

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

    # GIVEN that a gzipped-fastq file exists for the sample
    fastq_base_path: Path = tmp_path_factory.mktemp("fastq_files")
    fastq_file_path: Path = Path(fastq_base_path, "file.fastq.gz")
    shutil.copy2("tests/integration/config/file.fastq.gz", fastq_file_path)

    # GIVEN bundle data with the fastq files exists in Housekeeper
    bundle_data = {
        "name": sample.internal_id,
        "created": datetime.now(),
        "expires": datetime.now(),
        "files": [
            {
                "path": fastq_file_path.as_posix(),
                "archive": False,
                "tags": [sample.id, SequencingFileTag.FASTQ],
            },
        ],
    }

    bundle, version = cast(tuple[Bundle, Version], housekeeper_db.add_bundle(bundle_data))
    housekeeper_db.session.add(bundle)
    housekeeper_db.session.add(version)
    housekeeper_db.session.commit()

    # GIVEN that the Scout command returns exported panel data
    subprocess_mock = mocker.patch.object(commands, "subprocess")

    def mock_run(*args, **kwargs):
        command = args[0]
        stdout = b""

        if ("export" in command) and ("panel" in command):
            stdout += scout_export_panel_stdout
        return create_autospec(CompletedProcess, returncode=EXIT_SUCCESS, stdout=stdout, stderr=b"")

    subprocess_mock.run = Mock(side_effect=mock_run)

    # GIVEN an email address can be determined from the environment
    mocker.patch.object(mip_base, "environ_email", return_value="testuser@scilifelab.se")
    mocker.patch.object(analysis, "environ_email", return_value="testuser@scilifelab.se")
    mocker.patch.object(
        mip_dna_configurator, "environ_email", return_value="testuser@scilifelab.se"
    )

    # GIVEN the Trailblazer API returns no ongoing analysis for the case
    httpserver.expect_request(
        "/trailblazer/get-latest-analysis", data='{"case_id": "' + case.internal_id + '"}'
    ).respond_with_json(None)

    # GIVEN a pending analysis can be added to the Trailblazer API
    httpserver.expect_request(
        "/trailblazer/add-pending-analysis",
        data=b'{"case_id": "%(case_id)s", "email": "testuser@scilifelab.se", "type": "wgs", '
        b'"config_path": "%(case_dir)s/analysis/slurm_job_ids.yaml",'
        b' "order_id": 1, "out_dir": "%(case_dir)s/analysis", '
        b'"priority": "normal", "workflow": "MIP-DNA", "ticket": "%(ticket_id)s", '
        b'"workflow_manager": "slurm", "tower_workflow_id": null, "is_hidden": true}'
        % {
            b"case_id": case.internal_id.encode(),
            b"ticket_id": str(ticket_id).encode(),
            b"case_dir": str(Path(mip_dna_path, "cases", case.internal_id)).encode(),
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

    # GIVEN the analysis can be started as a sub process
    if test_command == "dev-start-available":
        analysis_subprocess_mock = mocker.patch.object(submitter, "subprocess")
    else:
        analysis_subprocess_mock = subprocess_mock

    # WHEN running mip-dna start-available
    result: Result = cli_runner.invoke(
        base,
        [
            "--config",
            config_path.as_posix(),
            "workflow",
            "mip-dna",
            test_command,
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
    # this will be fixed so that the order is always the same in the new implementation of
    # starting MIP-DNA pipelines
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

    # THEN a MIP-DNA analysis is started with the expected parameters
    test_command = (
        f"{mip_dna_path}/conda_bin run --name S_mip12.1 "
        f"{mip_dna_path}/bin analyse rd_dna --config {mip_dna_path}/config/mip12.1-dna-stage.yaml "
        f"{case.internal_id} --slurm_quality_of_service normal --email testuser@scilifelab.se"
    )

    analysis_subprocess_mock.run.assert_any_call(
        test_command,
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
    assert Path(case_dir, "pedigree.yaml").exists()


def create_qc_file(test_root_dir: Path, case: Case) -> Path:
    filepath = Path(
        f"{test_root_dir}/mip-dna/cases/{case.internal_id}/analysis/{case.internal_id}_qc_sample_info.yaml"
    )
    filepath.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2("tests/fixtures/apps/mip/dna/store/case_qc_sample_info.yaml", filepath)
    return filepath


def create_parsed_config(status_db_uri: str, housekeeper_db_uri: str, test_root_dir: str):
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
