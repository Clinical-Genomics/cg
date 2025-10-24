from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import ANY, Mock, call, create_autospec

import pytest
from click.testing import CliRunner, Result
from housekeeper.store.store import Store as HousekeeperStore
from pytest_httpserver import HTTPServer
from pytest_mock import MockerFixture

from cg.cli.base import base
from cg.constants.constants import CaseActions, Workflow
from cg.constants.process import EXIT_SUCCESS
from cg.constants.tb import AnalysisType
from cg.services.analysis_starter.configurator.file_creators import balsamic_config
from cg.store.models import Case, Order, Sample
from cg.store.store import Store
from cg.utils import commands
from tests.integration.conftest import (
    IntegrationTestPaths,
    copy_integration_test_file,
    create_integration_test_sample,
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
    housekeeper_db: HousekeeperStore,
    status_db: Store,
    test_run_paths: IntegrationTestPaths,
) -> Sample:

    return create_integration_test_sample(
        application_type=AnalysisType.TGS,
        flow_cell_id="sample_tgs_tumour_flow_cell",
        housekeeper_db=housekeeper_db,
        is_tumour=True,
        status_db=status_db,
        test_run_paths=test_run_paths,
    )


@pytest.fixture
def sample_wgs_normal(
    housekeeper_db: HousekeeperStore,
    status_db: Store,
    test_run_paths: IntegrationTestPaths,
) -> Sample:
    return create_integration_test_sample(
        application_type=AnalysisType.WGS,
        flow_cell_id="sample_wgs_normal_flow_cell",
        housekeeper_db=housekeeper_db,
        is_tumour=False,
        status_db=status_db,
        test_run_paths=test_run_paths,
    )


@pytest.fixture
def sample_wgs_tumour(
    housekeeper_db: HousekeeperStore,
    status_db: Store,
    test_run_paths: IntegrationTestPaths,
) -> Sample:
    return create_integration_test_sample(
        application_type=AnalysisType.WGS,
        flow_cell_id="sample_wgs_tumour_flow_cell",
        housekeeper_db=housekeeper_db,
        is_tumour=True,
        status_db=status_db,
        test_run_paths=test_run_paths,
    )


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


@pytest.fixture
def case_wgs_paired(
    helpers: StoreHelpers,
    sample_wgs_normal: Sample,
    sample_wgs_tumour: Sample,
    status_db: Store,
    ticket_id: int,
) -> Case:
    case: Case = helpers.add_case(
        store=status_db, data_analysis=Workflow.BALSAMIC, ticket=str(ticket_id)
    )
    order: Order = helpers.add_order(
        store=status_db, ticket_id=ticket_id, customer_id=case.customer_id
    )
    status_db.link_case_to_order(order_id=order.id, case_id=case.id)

    helpers.relate_samples(
        base_store=status_db, case=case, samples=[sample_wgs_normal, sample_wgs_tumour]
    )
    return case


@pytest.mark.xdist_group(name="integration")
@pytest.mark.integration
@pytest.mark.parametrize(
    "command",
    [
        "start-available",
        "dev-start-available",
    ],
)
def test_start_available_tgs_tumour_only(
    case_tgs_tumour_only: Case,
    command: str,
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
    balsamic_root_dir: Path = Path(test_root_dir, "balsamic_root_path")

    # GIVEN a case
    # GIVEN an order associated with the case
    # GIVEN a sample associated with the case
    # GIVEN a flow cell and sequencing run associated with the sample
    # GIVEN that a gzipped-fastq file exists for the sample
    # GIVEN bundle data with the fastq files exists in Housekeeper
    sample = sample_tgs_tumour
    case_id = case_tgs_tumour_only.internal_id

    # GIVEN a bed version exists and a corresponding bed name is returned by lims for the sample
    bed_name = "balsamic_integration_test_bed"
    helpers.ensure_bed_version(store=status_db, bed_name=bed_name)
    expect_lims_sample_request(lims_server=httpserver, sample=sample, bed_name=bed_name)

    # GIVEN a call to balsamic config case successfully generates a config file
    if command == "start-available":
        subprocess_mock = mocker.patch.object(commands, "subprocess")
    elif command == "dev-start-available":
        subprocess_mock = mocker.patch.object(balsamic_config, "subprocess")

    def mock_run(*args, **kwargs):
        command = args[0] if args else kwargs["args"]
        stdout = b""

        if "balsamic_binary_path config case" in command:
            create_tga_config_file(test_root_dir=test_root_dir, case=case_tgs_tumour_only)
        return create_autospec(CompletedProcess, returncode=EXIT_SUCCESS, stdout=stdout, stderr=b"")

    subprocess_mock.run = Mock(side_effect=mock_run)

    # GIVEN the Trailblazer API returns no ongoing analysis for the case
    httpserver.expect_request(
        "/trailblazer/get-latest-analysis",
        data='{"case_id": "' + case_id + '"}',
    ).respond_with_json(None)

    # GIVEN a new pending analysis can be added to the Trailblazer API
    case_path = Path(test_root_dir, "balsamic_root_path", case_id)
    expect_to_add_pending_analysis_to_trailblazer(
        trailblazer_server=httpserver,
        case=case_tgs_tumour_only,
        ticket_id=ticket_id,
        case_path=case_path,
        config_path=Path(case_path, "analysis", "slurm_jobids.yaml"),
        workflow=Workflow.BALSAMIC,
        analysis_type=AnalysisType.TGS,
    )

    # WHEN running balsamic start-available
    result: Result = cli_runner.invoke(
        base,
        [
            "--config",
            test_run_paths.cg_config_file.as_posix(),
            "workflow",
            "balsamic",
            command,
        ],
        catch_exceptions=False,
    )

    # THEN a successful exit code is returned
    assert result.exit_code == 0

    # THEN balsamic config case was called in the correct way
    expected_config_case_command = (
        f"{test_root_dir}/balsamic_conda_binary run --name conda_env_balsamic "
        f"{test_root_dir}/balsamic_binary_path config case "
        f"--analysis-dir {balsamic_root_dir} "
        f"--analysis-workflow balsamic "
        f"--balsamic-cache {test_root_dir}/balsamic_cache "
        f"--cadd-annotations {test_root_dir}/balsamic_cadd_path "
        f"--case-id {case_id} "
        f"--fastq-path {balsamic_root_dir}/{case_id}/fastq "
        f"--gender female "
        f"--genome-version hg19 "
        f"--gnomad-min-af5 {test_root_dir}/balsamic_gnomad_af5_path "
        f"--panel-bed {test_root_dir}/balsamic_bed_path/dummy_filename "
        f"--sentieon-install-dir {test_root_dir}/balsamic_sention_licence_path "
        f"--sentieon-license localhost "
        f"--tumor-sample-name {sample.internal_id}"
    )

    assert subprocess_mock.run.mock_calls[0] == call(
        expected_config_case_command,
        check=False,
        shell=True,
        stderr=ANY,
        stdout=ANY,
    )

    # THEN Balsamic run analysis was called in the correct way
    assert subprocess_mock.run.mock_calls[1] == call(
        f"{test_root_dir}/balsamic_conda_binary run --name conda_env_balsamic "
        f"{test_root_dir}/balsamic_binary_path run analysis "
        f"--account balsamic_slurm_account "
        f"--qos normal "
        f"--sample-config {balsamic_root_dir}/{case_id}/{case_id}.json "
        f"--headjob-partition head-jobs "
        f"--run-analysis",
        check=False,
        shell=True,
        stderr=ANY,
        stdout=ANY,
    )

    # THEN an analysis has been created for the case
    assert len(case_tgs_tumour_only.analyses) == 1

    # THEN the case action is set to running
    status_db.session.refresh(case_tgs_tumour_only)
    assert case_tgs_tumour_only.action == CaseActions.RUNNING


@pytest.mark.xdist_group(name="integration")
@pytest.mark.integration
def test_start_available_wgs_paired(
    case_wgs_paired: Case,
    sample_wgs_normal: Sample,
    sample_wgs_tumour: Sample,
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
    balsamic_root_dir: Path = Path(test_root_dir, "balsamic_root_path")

    # GIVEN a case
    # GIVEN an order associated with the case
    # GIVEN a tumour sample and a normal sample associated with the case
    # GIVEN a flow cell and sequencing run associated with the samples
    # GIVEN that a gzipped-fastq file exists for the sample
    # GIVEN bundle data with the fastq files exists in Housekeeper
    case_id = case_wgs_paired.internal_id

    # GIVEN a bed version exists and a corresponding bed name is returned by lims for the sample
    bed_name = "balsamic_integration_test_bed"
    helpers.ensure_bed_version(store=status_db, bed_name=bed_name)
    expect_lims_sample_request(lims_server=httpserver, sample=sample_wgs_normal, bed_name=bed_name)
    expect_lims_sample_request(lims_server=httpserver, sample=sample_wgs_tumour, bed_name=bed_name)

    # GIVEN a call to balsamic config case successfully generates a config file
    subprocess_mock = mocker.patch.object(commands, "subprocess")

    def mock_run(*args, **kwargs):
        command = args[0]
        stdout = b""

        if "balsamic_binary_path config case" in command:
            create_wgs_config_file(test_root_dir=test_root_dir, case=case_wgs_paired)
        return create_autospec(CompletedProcess, returncode=EXIT_SUCCESS, stdout=stdout, stderr=b"")

    subprocess_mock.run = Mock(side_effect=mock_run)

    # GIVEN the Trailblazer API returns no ongoing analysis for the case
    httpserver.expect_request(
        "/trailblazer/get-latest-analysis",
        data='{"case_id": "' + case_id + '"}',
    ).respond_with_json(None)

    # GIVEN a new pending analysis can be added to the Trailblazer API
    case_path = Path(test_root_dir, "balsamic_root_path", case_id)
    expect_to_add_pending_analysis_to_trailblazer(
        trailblazer_server=httpserver,
        case=case_wgs_paired,
        ticket_id=ticket_id,
        case_path=case_path,
        config_path=Path(case_path, "analysis", "slurm_jobids.yaml"),
        workflow=Workflow.BALSAMIC,
        analysis_type=AnalysisType.WGS,
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
        catch_exceptions=False,
    )

    # THEN a successful exit code is returned
    assert result.exit_code == 0

    # THEN balsamic config case was called in the correct way
    expected_config_case_command = (
        f"{test_root_dir}/balsamic_conda_binary run --name conda_env_balsamic "
        f"{test_root_dir}/balsamic_binary_path config case "
        f"--analysis-dir {balsamic_root_dir} "
        f"--analysis-workflow balsamic "
        f"--balsamic-cache {test_root_dir}/balsamic_cache "
        f"--cadd-annotations {test_root_dir}/balsamic_cadd_path "
        f"--artefact-sv-observations {test_root_dir}/loqusdb/loqusdb_artefact_somatic_sv_variants_export-20250920-.vcf.gz "
        f"--case-id {case_id} "
        f"--fastq-path {balsamic_root_dir}/{case_id}/fastq "
        f"--gender female "
        f"--genome-interval {test_root_dir}/balsamic_genome_interval_path "
        f"--genome-version hg19 "
        f"--gens-coverage-pon {test_root_dir}/balsamic_gens_coverage_female_path "
        f"--gnomad-min-af5 {test_root_dir}/balsamic_gnomad_af5_path "
        f"--normal-sample-name {sample_wgs_normal.internal_id} "
        f"--sentieon-install-dir {test_root_dir}/balsamic_sention_licence_path "
        f"--sentieon-license localhost "
        f"--tumor-sample-name {sample_wgs_tumour.internal_id}"
    )

    assert subprocess_mock.run.mock_calls[0] == call(
        expected_config_case_command,
        check=False,
        shell=True,
        stderr=ANY,
        stdout=ANY,
    )

    # THEN balsamic run analysis was called in the correct way
    assert subprocess_mock.run.mock_calls[1] == call(
        f"{test_root_dir}/balsamic_conda_binary run --name conda_env_balsamic "
        f"{test_root_dir}/balsamic_binary_path run analysis "
        f"--account balsamic_slurm_account "
        f"--qos normal "
        f"--sample-config {balsamic_root_dir}/{case_id}/{case_id}.json "
        f"--headjob-partition head-jobs "
        f"--run-analysis",
        check=False,
        shell=True,
        stderr=ANY,
        stdout=ANY,
    )

    # THEN an analysis has been created for the case
    assert len(case_wgs_paired.analyses) == 1

    # THEN the case action is set to running
    status_db.session.refresh(case_wgs_paired)
    assert case_wgs_paired.action == CaseActions.RUNNING


def create_tga_config_file(test_root_dir: Path, case: Case) -> Path:
    filepath = Path(
        f"{test_root_dir}/balsamic_root_path/{case.internal_id}/{case.internal_id}.json"
    )
    copy_integration_test_file(
        from_path=Path("tests/fixtures/apps/balsamic/tga_case/config.json"), to_path=filepath
    )
    return filepath


def create_wgs_config_file(test_root_dir: Path, case: Case) -> Path:
    filepath = Path(
        f"{test_root_dir}/balsamic_root_path/{case.internal_id}/{case.internal_id}.json"
    )

    copy_integration_test_file(
        from_path=Path("tests/fixtures/apps/balsamic/wgs_case/config.json"), to_path=filepath
    )
    return filepath


def expect_lims_sample_request(lims_server: HTTPServer, sample: Sample, bed_name: str):
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
