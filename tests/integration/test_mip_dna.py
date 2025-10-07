import shutil
from datetime import datetime
from pathlib import Path
from subprocess import CompletedProcess
from typing import cast
from unittest.mock import ANY, Mock, create_autospec

import pytest
from click.testing import CliRunner, Result
from housekeeper.store.models import Bundle, Version
from housekeeper.store.store import Store as HousekeeperStore
from pytest import TempPathFactory
from pytest_httpserver import HTTPServer
from pytest_mock import MockerFixture

from cg.apps.environ import environ_email
from cg.cli.base import base
from cg.constants.constants import CaseActions, Workflow
from cg.constants.gene_panel import GenePanelMasterList
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.constants.process import EXIT_SUCCESS
from cg.constants.tb import AnalysisType
from cg.services.analysis_starter.submitters.subprocess import submitter
from cg.store.models import Case, IlluminaFlowCell, IlluminaSequencingRun, Order, Sample
from cg.store.store import Store
from cg.utils import commands
from tests.integration.conftest import (
    IntegrationTestPaths,
    expect_to_add_pending_analysis_to_trailblazer,
)
from tests.store_helpers import StoreHelpers


@pytest.fixture(autouse=True)
def current_workflow() -> Workflow:
    return Workflow.MIP_DNA


@pytest.fixture
def scout_export_panel_stdout() -> bytes:
    return b"22\t26995242\t27014052\t2397\tCRYBB1\n22\t38452318\t38471708\t9394\tPICK1\n"


@pytest.fixture
def scout_export_manged_variants_stdout() -> bytes:
    return b"""##fileformat=VCFv4.2
##INFO=<ID=END,Number=1,Type=Integer,Description="End position of the variant described in this record">
##fileDate=2023-12-07 16:35:38.814086
##INFO=<ID=SVTYPE,Number=1,Type=String,Description="Type of structural variant">
##INFO=<ID=TYPE,Number=1,Type=String,Description="Type of variant">
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
1	48696925	.	G	C	.		END=48696925;TYPE=SNV
14	76548781	.	CTGGACC	G	.		END=76548781;TYPE=INDEL"""


@pytest.mark.xdist_group(name="integration")
@pytest.mark.parametrize(
    "test_command",
    ["start-available", "dev-start-available"],
)
@pytest.mark.integration
def test_start_available_mip_dna(
    test_command: str,
    test_run_paths: IntegrationTestPaths,
    helpers: StoreHelpers,
    housekeeper_db: HousekeeperStore,
    httpserver: HTTPServer,
    mocker: MockerFixture,
    scout_export_panel_stdout: bytes,
    scout_export_manged_variants_stdout: bytes,
    status_db: Store,
    tmp_path_factory: TempPathFactory,
):
    """Test a successful run of the command 'cg workflow mip-dna start-available'
    with one case to be analysed that has not been analysed before."""
    cli_runner = CliRunner()

    # GIVEN a MIP-DNA root directory
    test_root_dir: Path = test_run_paths.test_root_dir

    # GIVEN a config file with valid database URIs and directories
    config_path: Path = test_run_paths.cg_config_file

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
        elif ("export" in command) and ("managed" in command):
            stdout += scout_export_manged_variants_stdout
        return create_autospec(CompletedProcess, returncode=EXIT_SUCCESS, stdout=stdout, stderr=b"")

    subprocess_mock.run = Mock(side_effect=mock_run)

    # GIVEN an email address can be determined from the environment
    email: str = environ_email()

    # GIVEN the Trailblazer API returns no ongoing analysis for the case
    httpserver.expect_request(
        "/trailblazer/get-latest-analysis", data='{"case_id": "' + case.internal_id + '"}'
    ).respond_with_json(None)

    # GIVEN a new pending analysis can be added to the Trailblazer API
    case_path = Path(mip_dna_path, "cases", case.internal_id)
    expect_to_add_pending_analysis_to_trailblazer(
        trailblazer_server=httpserver,
        case=case,
        ticket_id=ticket_id,
        case_path=case_path,
        config_path=Path(case_path, "analysis", "slurm_job_ids.yaml"),
        workflow=Workflow.MIP_DNA,
        type=AnalysisType.WGS,
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
        catch_exceptions=False,
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
    expected_command = (
        f"{mip_dna_path}/conda_bin run --name S_mip12.1 "
        f"{mip_dna_path}/bin analyse rd_dna --config {mip_dna_path}/config/mip12.1-dna-stage.yaml "
        f"{case.internal_id} --slurm_quality_of_service normal --email {email}"
    )

    if test_command == "dev-start-available":
        analysis_subprocess_mock.run.assert_any_call(
            args=expected_command,
            check=False,
            shell=True,
            stdout=ANY,
            stderr=ANY,
        )
    else:
        analysis_subprocess_mock.run.assert_any_call(
            expected_command,
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

    # THEN the pedigree file has been created with the correct contents
    case_dir = Path(test_root_dir, "mip-dna", "cases", case.internal_id)

    expected_pedigree_content: str = f"""---
case: {case.internal_id}
default_gene_panels:
- panel_test
samples:
- analysis_type: wgs
  capture_kit: twistexomecomprehensive_10.2_hg19_design.bed
  expected_coverage: 30
  father: '0'
  mother: '0'
  phenotype: unaffected
  sample_display_name: sample_test
  sample_id: {sample.internal_id}
  sex: female
"""
    with open(Path(case_dir, "pedigree.yaml")) as f:
        assert f.read() == expected_pedigree_content

    # THEN the managed_variants file has been created with the correct contents
    expected_managed_variants_content: str = scout_export_manged_variants_stdout.decode()
    with open(Path(case_dir, "managed_variants.vcf")) as f:
        assert f.read() == expected_managed_variants_content

    # THEN the gene_panels file has been created with the correct contents
    expected_gene_panels_content: str = scout_export_panel_stdout.decode().removesuffix("\n")
    with open(Path(case_dir, "gene_panels.bed")) as f:
        assert f.read() == expected_gene_panels_content


def create_qc_file(test_root_dir: Path, case: Case) -> Path:
    filepath = Path(
        f"{test_root_dir}/mip-dna/cases/{case.internal_id}/analysis/{case.internal_id}_qc_sample_info.yaml"
    )
    filepath.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2("tests/fixtures/apps/mip/dna/store/case_qc_sample_info.yaml", filepath)
    return filepath
