import shutil
from datetime import datetime
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import ANY, Mock, create_autospec

import pytest
from click.testing import CliRunner, Result
from housekeeper.store.store import Store as HousekeeperStore
from pytest_httpserver import HTTPServer
from pytest_mock import MockerFixture

from cg.cli.base import base
from cg.constants.constants import CaseActions, Workflow
from cg.constants.process import EXIT_SUCCESS
from cg.constants.tb import AnalysisType
from cg.store.models import Case, IlluminaFlowCell, IlluminaSequencingRun, Order, Sample
from cg.store.store import Store
from cg.utils import commands
from tests.integration.conftest import (
    IntegrationTestPaths,
    create_fastq_file_and_add_to_housekeeper,
    expect_to_add_pending_analysis_to_trailblazer,
)
from tests.store_helpers import StoreHelpers


@pytest.fixture(autouse=True)
def current_workflow() -> Workflow:
    return Workflow.BALSAMIC


@pytest.fixture
def ticket_id() -> int:
    return 12345


@pytest.fixture
def sample_tgs_tumour(
    helpers: StoreHelpers,
    housekeeper_db: HousekeeperStore,
    status_db: Store,
    test_run_paths: IntegrationTestPaths,
) -> Sample:
    sample: Sample = helpers.add_sample(
        store=status_db,
        is_tumour=True,
        last_sequenced_at=datetime.now(),
        application_type=AnalysisType.TGS,
    )
    flow_cell: IlluminaFlowCell = helpers.add_illumina_flow_cell(store=status_db)
    sequencing_run: IlluminaSequencingRun = helpers.add_illumina_sequencing_run(
        store=status_db, flow_cell=flow_cell
    )
    helpers.add_illumina_sample_sequencing_metrics_object(
        store=status_db, sample_id=sample.internal_id, sequencing_run=sequencing_run, lane=1
    )

    create_fastq_file_and_add_to_housekeeper(
        housekeeper_db=housekeeper_db, test_root_dir=test_run_paths.test_root_dir, sample=sample
    )

    return sample


@pytest.fixture
def case_tgs_tumour_only(
    helpers: StoreHelpers, status_db: Store, sample_tgs_tumour: Sample, ticket_id: int
) -> Case:
    case: Case = helpers.add_case(
        store=status_db, data_analysis=Workflow.BALSAMIC, ticket=str(ticket_id)
    )
    order: Order = helpers.add_order(
        store=status_db, ticket_id=ticket_id, customer_id=case.customer_id
    )
    status_db.link_case_to_order(order_id=order.id, case_id=case.id)

    helpers.relate_samples(base_store=status_db, case=case, samples=[sample_tgs_tumour])
    return case


@pytest.mark.xdist_group(name="integration")
@pytest.mark.integration
def test_start_available(
    case_tgs_tumour_only: Case,
    sample_tgs_tumour: Sample,
    test_run_paths: IntegrationTestPaths,
    helpers: StoreHelpers,
    httpserver: HTTPServer,
    mocker: MockerFixture,
    status_db: Store,
    ticket_id: int,
):
    cli_runner = CliRunner()

    # GIVEN a Balsamic root dir
    test_root_dir: Path = test_run_paths.test_root_dir

    # GIVEN a case
    # GIVEN an order associated with the case
    # GIVEN a sample associated with the case
    # GIVEN a flow cell and sequencing run associated with the sample
    # GIVEN that a gzipped-fastq file exists for the sample
    # GIVEN bundle data with the fastq files exists in Housekeeper
    case = case_tgs_tumour_only
    sample = sample_tgs_tumour

    # GIVEN a bed version exists and a corresponding bed name is returned by lims for the sample
    bed_name = "balsamic_integration_test_bed"
    helpers.ensure_bed_version(store=status_db, bed_name=bed_name)
    expect_lims_sample_request(lims_server=httpserver, sample=sample_tgs_tumour, bed_name=bed_name)

    # GIVEN a call to balsamic config case successfully generates a config file
    subprocess_mock = mocker.patch.object(commands, "subprocess")

    def mock_run(*args, **kwargs):
        command = args[0]
        stdout = b""

        if "balsamic_binary_path config case" in command:
            create_tga_config_file(test_root_dir=test_root_dir, case=case)
        return create_autospec(CompletedProcess, returncode=EXIT_SUCCESS, stdout=stdout, stderr=b"")

    subprocess_mock.run = Mock(side_effect=mock_run)

    # GIVEN the Trailblazer API returns no ongoing analysis for the case
    httpserver.expect_request(
        "/trailblazer/get-latest-analysis", data='{"case_id": "' + case.internal_id + '"}'
    ).respond_with_json(None)

    # GIVEN a new pending analysis can be added to the Trailblazer API
    case_path = Path(test_root_dir, "balsamic_root_path", case.internal_id)
    expect_to_add_pending_analysis_to_trailblazer(
        trailblazer_server=httpserver,
        case=case,
        ticket_id=ticket_id,
        case_path=case_path,
        config_path=Path(case_path, "analysis", "slurm_jobids.yaml"),
        workflow=Workflow.BALSAMIC,
        type=AnalysisType.TGS,
    )

    # WHEN running balsamic start-available
    result: Result = cli_runner.invoke(
        base,
        [
            "--config",
            test_run_paths.cg_config_file.as_posix(),
            "workflow",
            "balsamic",
            "start-available",
        ],
    )

    assert result.exception is None

    # THEN balsamic config case was called in the correct way
    expected_config_case_command = (
        f"{test_root_dir}/balsamic_conda_binary run --name conda_env_balsamic "
        f"{test_root_dir}/balsamic_binary_path config case "
        f"--analysis-dir {test_root_dir}/balsamic_root_path "
        f"--analysis-workflow balsamic "
        f"--balsamic-cache {test_root_dir}/balsamic_cache "
        f"--cadd-annotations {test_root_dir}/balsamic_cadd_path "
        f"--case-id {case.internal_id} "
        f"--fastq-path {test_root_dir}/balsamic_root_path/{case.internal_id}/fastq "
        f"--gender female "
        f"--genome-version hg19 "
        f"--gnomad-min-af5 {test_root_dir}/balsamic_gnomad_af5_path "
        f"--panel-bed {test_root_dir}/balsamic_bed_path/dummy_filename "
        f"--sentieon-install-dir {test_root_dir}/balsamic_sention_licence_path "
        f"--sentieon-license localhost "
        f"--tumor-sample-name {sample.internal_id}"
    )

    subprocess_mock.run.assert_any_call(
        expected_config_case_command,
        check=False,
        shell=True,
        stderr=ANY,
        stdout=ANY,
    )

    # THEN balsamic run analysis was called in the correct way
    subprocess_mock.run.assert_any_call(
        f"{test_root_dir}/balsamic_conda_binary run --name conda_env_balsamic "
        f"{test_root_dir}/balsamic_binary_path run analysis "
        f"--account balsamic_slurm_account "
        f"--mail-user balsamic_mail_user@scilifelab.se "
        f"--qos normal "
        f"--sample-config {test_root_dir}/balsamic_root_path/{case.internal_id}/{case.internal_id}.json "
        f"--run-analysis --benchmark",
        check=False,
        shell=True,
        stderr=ANY,
        stdout=ANY,
    )

    # THEN an analysis has been created for the case
    assert len(case.analyses) == 1

    # THEN the case action is set to running
    status_db.session.refresh(case)
    assert case.action == CaseActions.RUNNING


def create_tga_config_file(test_root_dir: Path, case: Case) -> Path:
    filepath = Path(
        f"{test_root_dir}/balsamic_root_path/{case.internal_id}/{case.internal_id}.json"
    )
    filepath.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2("tests/fixtures/apps/balsamic/tga_case/config.json", filepath)
    return filepath


def expect_lims_sample_request(lims_server, sample, bed_name):
    lims_server.expect_request(f"/lims/api/v2/samples/{sample.internal_id}").respond_with_data(
        f"""<smp:sample xmlns:udf="http://genologics.com/ri/userdefined" xmlns:ri="http://genologics.com/ri" xmlns:file="http://genologics.com/ri/file" xmlns:smp="http://genologics.com/ri/sample" uri="http://127.0.0.1:8000/api/v2/samples/ACC2351A1" limsid="ACC2351A1">
<name>2016-02293</name>
<date-received>2017-02-16</date-received>
<project limsid="ACC2351" uri="http://127.0.0.1:8000/api/v2/projects/ACC2351"/>
<submitter uri="http://127.0.0.1:8000/api/v2/researchers/3">
<first-name>API</first-name>
<last-name>Access</last-name>
</submitter>
<artifact limsid="ACC2351A1PA1" uri="http://127.0.0.1:8000/api/v2/artifacts/ACC2351A1PA1?state=55264"/>
<udf:field type="Boolean" name="Sample Delivered">true</udf:field>
<udf:field type="String" name="Concentration (nM)">NA</udf:field>
<udf:field type="String" name="customer">cust002</udf:field>
<udf:field type="String" name="familyID">F0005063</udf:field>
<udf:field type="String" name="Gender">M</udf:field>
<udf:field type="String" name="priority">standard</udf:field>
<udf:field type="String" name="Process only if QC OK">NA</udf:field>
<udf:field type="Numeric" name="Reads missing (M)">0</udf:field>
<udf:field type="String" name="Reference Genome Microbial">NA</udf:field>
<udf:field type="String" name="Sample Buffer">NA</udf:field>
<udf:field type="String" name="Sequencing Analysis">EXXCUSR000</udf:field>
<udf:field type="String" name="Status">unaffected</udf:field>
<udf:field type="String" name="Strain">NA</udf:field>
<udf:field type="String" name="Source">NA</udf:field>
<udf:field type="String" name="Volume (uL)">NA</udf:field>
<udf:field type="String" name="Gene List">OMIM-AUTO</udf:field>
<udf:field type="String" name="Index type">NA</udf:field>
<udf:field type="String" name="Data Analysis">scout</udf:field>
<udf:field type="String" name="Index number">NA</udf:field>
<udf:field type="String" name="Application Tag Version">1</udf:field>
<udf:field type="String" name="Bait Set">{bed_name}</udf:field>
<udf:field type="String" name="Capture Library version">Agilent Sureselect V5</udf:field>
</smp:sample>""",
        content_type="application/xml",
    )
