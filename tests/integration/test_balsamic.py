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
from cg.constants.observations import BalsamicObservationPanel
from cg.constants.process import EXIT_SUCCESS
from cg.constants.tb import AnalysisType
from cg.services.analysis_starter.configurator.file_creators import balsamic_config
from cg.services.analysis_starter.submitters.subprocess import submitter
from cg.store.models import Case, Order, Sample
from cg.store.store import Store
from cg.utils import commands
from tests.integration.conftest import IntegrationTestPaths
from tests.integration.utils import (
    copy_integration_test_file,
    create_empty_file,
    create_integration_test_sample_fastq_files,
    expect_to_add_pending_analysis_to_trailblazer,
    expect_lims_sample_request
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

    return create_integration_test_sample_fastq_files(
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
    return create_integration_test_sample_fastq_files(
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
    return create_integration_test_sample_fastq_files(
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
    bed_name = BalsamicObservationPanel.MYELOID
    helpers.ensure_bed_version(store=status_db, bed_name=bed_name)
    expect_lims_sample_request(lims_server=httpserver, sample=sample, bed_name=bed_name)

    # GIVEN files exists on disk for all flags requiring a file
    _create_files_for_flags(test_root_dir)

    # GIVEN a call to balsamic config case successfully generates a config file
    match command:
        case "start-available":
            config_case_subprocess_mock = mocker.patch.object(commands, "subprocess")
            run_analysis_subprocess_mock = config_case_subprocess_mock
        case "dev-start-available":
            config_case_subprocess_mock = mocker.patch.object(balsamic_config, "subprocess")
            run_analysis_subprocess_mock = mocker.patch.object(submitter, "subprocess")

    def mock_run(*args, **kwargs):
        command = args[0] if args else kwargs["args"]
        stdout = b""

        if "balsamic_binary_path config case" in command:
            _create_tga_config_file(test_root_dir=test_root_dir, case=case_tgs_tumour_only)
        return create_autospec(CompletedProcess, returncode=EXIT_SUCCESS, stdout=stdout, stderr=b"")

    config_case_subprocess_mock.run = Mock(side_effect=mock_run)

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
        out_dir=Path(case_path, "analysis"),
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

    # THEN Balsamic config case was called in the correct way
    first_call = config_case_subprocess_mock.run.mock_calls[0]

    expected_config_case_command = (
        f"{test_root_dir}/balsamic_conda_binary run --name conda_env_balsamic "
        f"{test_root_dir}/balsamic_binary_path config case "
        f"--analysis-dir {balsamic_root_dir} "
        f"--analysis-workflow balsamic "
        f"--artefact-snv-observations {test_root_dir}/loqusdb/artefact_somatic_snv.vcf.gz "
        f"--balsamic-cache {test_root_dir}/balsamic_cache "
        f"--cadd-annotations {test_root_dir}/balsamic_cadd_path "
        f"--cancer-germline-snv-observations {test_root_dir}/loqusdb/cancer_germline_snv.vcf.gz "
        f"--cancer-somatic-snv-observations {test_root_dir}/loqusdb/cancer_somatic_snv.vcf.gz "
        f"--cancer-somatic-snv-panel-observations {test_root_dir}/loqusdb/loqusdb_cancer_somatic_myeloid_snv_variants_export-20250920-.vcf.gz "
        f"--cancer-somatic-sv-observations {test_root_dir}/loqusdb/cancer_somatic_sv.vcf.gz "
        f"--case-id {case_id} "
        f"--clinical-snv-observations {test_root_dir}/loqusdb/clinical_snv.vcf.gz "
        f"--clinical-sv-observations {test_root_dir}/loqusdb/clinical_sv.vcf.gz "
        f"--fastq-path {balsamic_root_dir}/{case_id}/fastq "
        f"--gender female "
        f"--genome-version hg19 "
        f"--gnomad-min-af5 {test_root_dir}/balsamic_gnomad_af5_path "
        f"--panel-bed {test_root_dir}/balsamic_bed_path/dummy_filename "
        f"--sentieon-install-dir {test_root_dir}/balsamic_sention_licence_path "
        f"--sentieon-license localhost "
        f"--swegen-snv {test_root_dir}/swegen/swegen_snv.vcf.gz "
        f"--swegen-sv {test_root_dir}/swegen/swegen_sv.vcf.gz "
        f"--tumor-sample-name {sample.internal_id}"
    )

    match command:
        case "start-available":
            assert first_call == call(
                expected_config_case_command,
                check=False,
                shell=True,
                stderr=ANY,
                stdout=ANY,
            )
        case "dev-start-available":
            assert first_call == call(
                args=expected_config_case_command,
                check=False,
                shell=True,
                stderr=ANY,
                stdout=ANY,
            )

    # THEN Balsamic run analysis was called in the correct way
    expected_run_analysis_command = (
        f"{test_root_dir}/balsamic_conda_binary run --name conda_env_balsamic "
        f"{test_root_dir}/balsamic_binary_path run analysis "
        f"--account balsamic_slurm_account "
        f"--qos normal "
        f"--sample-config {balsamic_root_dir}/{case_id}/{case_id}.json "
        f"--headjob-partition head-jobs "
        f"--run-analysis"
    )

    match command:
        case "start-available":
            run_analysis_call = run_analysis_subprocess_mock.run.mock_calls[1]

            assert run_analysis_call == call(
                expected_run_analysis_command,
                check=False,
                shell=True,
                stderr=ANY,
                stdout=ANY,
            )

        case "dev-start-available":
            run_analysis_call = run_analysis_subprocess_mock.run.mock_calls[0]

            assert run_analysis_call == call(
                args=expected_run_analysis_command,
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
@pytest.mark.parametrize(
    "command",
    [
        "start-available",
        "dev-start-available",
    ],
)
def test_start_available_wgs_paired(
    case_wgs_paired: Case,
    command: str,
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

    # GIVEN files exists on disk for all flags requiring a file
    _create_files_for_flags(test_root_dir)

    # GIVEN a call to balsamic config case successfully generates a config file
    match command:
        case "start-available":
            config_case_subprocess_mock = mocker.patch.object(commands, "subprocess")
            run_analysis_subprocess_mock = config_case_subprocess_mock
        case "dev-start-available":
            config_case_subprocess_mock = mocker.patch.object(balsamic_config, "subprocess")
            run_analysis_subprocess_mock = mocker.patch.object(submitter, "subprocess")

    def mock_run(*args, **kwargs):
        command = args[0] if args else kwargs["args"]
        stdout = b""

        if "balsamic_binary_path config case" in command:
            _create_wgs_config_file(test_root_dir=test_root_dir, case=case_wgs_paired)
        return create_autospec(CompletedProcess, returncode=EXIT_SUCCESS, stdout=stdout, stderr=b"")

    config_case_subprocess_mock.run = Mock(side_effect=mock_run)

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
        out_dir=Path(case_path, "analysis"),
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
            command,
        ],
        catch_exceptions=False,
    )

    # THEN a successful exit code is returned
    assert result.exit_code == 0

    # THEN balsamic config case was called in the correct way
    first_call = config_case_subprocess_mock.run.mock_calls[0]
    expected_config_case_command = (
        f"{test_root_dir}/balsamic_conda_binary run --name conda_env_balsamic "
        f"{test_root_dir}/balsamic_binary_path config case "
        f"--analysis-dir {balsamic_root_dir} "
        f"--analysis-workflow balsamic "
        f"--artefact-snv-observations {test_root_dir}/loqusdb/artefact_somatic_snv.vcf.gz "
        f"--artefact-sv-observations {test_root_dir}/loqusdb/loqusdb_artefact_somatic_sv_variants_export-20250920-.vcf.gz "
        f"--balsamic-cache {test_root_dir}/balsamic_cache "
        f"--cadd-annotations {test_root_dir}/balsamic_cadd_path "
        f"--cancer-germline-snv-observations {test_root_dir}/loqusdb/cancer_germline_snv.vcf.gz "
        f"--cancer-somatic-snv-observations {test_root_dir}/loqusdb/cancer_somatic_snv.vcf.gz "
        f"--cancer-somatic-sv-observations {test_root_dir}/loqusdb/cancer_somatic_sv.vcf.gz "
        f"--case-id {case_id} "
        f"--clinical-snv-observations {test_root_dir}/loqusdb/clinical_snv.vcf.gz "
        f"--clinical-sv-observations {test_root_dir}/loqusdb/clinical_sv.vcf.gz "
        f"--fastq-path {balsamic_root_dir}/{case_id}/fastq "
        f"--gender female "
        f"--genome-interval {test_root_dir}/balsamic_genome_interval_path "
        f"--genome-version hg19 "
        f"--gens-coverage-pon {test_root_dir}/balsamic_gens_coverage_female_path "
        f"--gnomad-min-af5 {test_root_dir}/balsamic_gnomad_af5_path "
        f"--normal-sample-name {sample_wgs_normal.internal_id} "
        f"--sentieon-install-dir {test_root_dir}/balsamic_sention_licence_path "
        f"--sentieon-license localhost "
        f"--swegen-snv {test_root_dir}/swegen/swegen_snv.vcf.gz "
        f"--swegen-sv {test_root_dir}/swegen/swegen_sv.vcf.gz "
        f"--tumor-sample-name {sample_wgs_tumour.internal_id}"
    )

    match command:
        case "start-available":
            assert first_call == call(
                expected_config_case_command,
                check=False,
                shell=True,
                stderr=ANY,
                stdout=ANY,
            )

        case "dev-start-available":
            assert first_call == call(
                args=expected_config_case_command,
                check=False,
                shell=True,
                stderr=ANY,
                stdout=ANY,
            )

    # THEN Balsamic run analysis was called in the correct way
    expected_run_analysis_command = (
        f"{test_root_dir}/balsamic_conda_binary run --name conda_env_balsamic "
        f"{test_root_dir}/balsamic_binary_path run analysis "
        f"--account balsamic_slurm_account "
        f"--qos normal "
        f"--sample-config {balsamic_root_dir}/{case_id}/{case_id}.json "
        f"--headjob-partition head-jobs "
        f"--run-analysis"
    )

    match command:
        case "start-available":
            run_analysis_call = run_analysis_subprocess_mock.run.mock_calls[1]

            assert run_analysis_call == call(
                expected_run_analysis_command,
                check=False,
                shell=True,
                stderr=ANY,
                stdout=ANY,
            )

        case "dev-start-available":
            run_analysis_call = run_analysis_subprocess_mock.run.mock_calls[0]

            assert run_analysis_call == call(
                args=expected_run_analysis_command,
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


def _create_files_for_flags(test_root_dir: Path):
    create_empty_file(Path(test_root_dir, "loqusdb", "artefact_somatic_snv.vcf.gz"))
    create_empty_file(Path(test_root_dir, "loqusdb", "cancer_germline_snv.vcf.gz"))
    create_empty_file(Path(test_root_dir, "loqusdb", "cancer_somatic_snv.vcf.gz"))
    create_empty_file(Path(test_root_dir, "loqusdb", "cancer_somatic_sv.vcf.gz"))
    create_empty_file(Path(test_root_dir, "loqusdb", "clinical_snv.vcf.gz"))
    create_empty_file(Path(test_root_dir, "loqusdb", "clinical_sv.vcf.gz"))
    create_empty_file(Path(test_root_dir, "swegen", "swegen_snv.vcf.gz"))
    create_empty_file(Path(test_root_dir, "swegen", "swegen_sv.vcf.gz"))


def _create_tga_config_file(test_root_dir: Path, case: Case) -> Path:
    filepath = Path(
        f"{test_root_dir}/balsamic_root_path/{case.internal_id}/{case.internal_id}.json"
    )
    copy_integration_test_file(
        from_path=Path("tests/fixtures/apps/balsamic/tga_case/config.json"), to_path=filepath
    )
    return filepath


def _create_wgs_config_file(test_root_dir: Path, case: Case) -> Path:
    filepath = Path(
        f"{test_root_dir}/balsamic_root_path/{case.internal_id}/{case.internal_id}.json"
    )

    copy_integration_test_file(
        from_path=Path("tests/fixtures/apps/balsamic/wgs_case/config.json"), to_path=filepath
    )
    return filepath
