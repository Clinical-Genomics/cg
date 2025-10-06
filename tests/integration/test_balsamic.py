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
from pytest_httpserver import HTTPServer
from pytest_mock import MockerFixture

from cg.cli.base import base
from cg.constants.constants import Workflow
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.constants.process import EXIT_SUCCESS
from cg.constants.tb import AnalysisType
from cg.store.models import Case, IlluminaFlowCell, IlluminaSequencingRun, Order, Sample
from cg.store.store import Store
from cg.utils import commands
from tests.integration.conftest import TestRunPaths, expect_to_add_pending_analysis_to_trailblazer
from tests.store_helpers import StoreHelpers


@pytest.fixture(autouse=True)
def current_workflow() -> Workflow:
    return Workflow.BALSAMIC


@pytest.mark.xdist_group(name="integration")
@pytest.mark.integration
def test_start_available(
    test_run_paths: TestRunPaths,
    helpers: StoreHelpers,
    housekeeper_db: HousekeeperStore,
    httpserver: HTTPServer,
    mocker: MockerFixture,
    status_db: Store,
    tmp_path_factory: pytest.TempPathFactory,
):
    cli_runner = CliRunner()

    # GIVEN a case
    ticket_id = 12345
    case: Case = helpers.add_case(
        store=status_db, data_analysis=Workflow.BALSAMIC, ticket=str(ticket_id)
    )

    # GIVEN an order associated with the case
    order: Order = helpers.add_order(
        store=status_db, ticket_id=ticket_id, customer_id=case.customer_id
    )
    status_db.link_case_to_order(order_id=order.id, case_id=case.id)

    # GIVEN a sample associated with the case
    sample: Sample = helpers.add_sample(
        store=status_db,
        last_sequenced_at=datetime.now(),
        application_type=AnalysisType.TGS,
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

    bed_name = "balsamic_integration_test_bed"
    helpers.ensure_bed_version(store=status_db, bed_name=bed_name)

    expect_lims_sample_request(lims_server=httpserver, sample=sample, bed_name=bed_name)

    # GIVEN a call to balsamic config case successfully generates a config file
    subprocess_mock = mocker.patch.object(commands, "subprocess")

    def mock_run(*args, **kwargs):
        command = args[0]
        stdout = b""

        if "balsamic_binary_path config case" in command:
            create_tga_config_file(test_root_dir=test_run_paths.test_root_dir, case=case)
        return create_autospec(CompletedProcess, returncode=EXIT_SUCCESS, stdout=stdout, stderr=b"")

    subprocess_mock.run = Mock(side_effect=mock_run)

    # GIVEN the Trailblazer API returns no ongoing analysis for the case
    httpserver.expect_request(
        "/trailblazer/get-latest-analysis", data='{"case_id": "' + case.internal_id + '"}'
    ).respond_with_json(None)

    # GIVEN a new pending analysis can be added to the Trailblazer API
    case_path = Path(test_run_paths.test_root_dir, "balsamic_root_path", case.internal_id)
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


@pytest.mark.xdist_group(name="integration")
@pytest.mark.integration
def test_start_config_case(
    test_run_paths: TestRunPaths,
    helpers: StoreHelpers,
    httpserver: HTTPServer,
    mocker: MockerFixture,
    status_db: Store,
):
    cli_runner = CliRunner()
    cg_config_file = test_run_paths.cg_config_file

    # GIVEN a config file with valid database URIs and directories

    test_root_dir = test_run_paths.test_root_dir

    # GIVEN a case
    ticket_id = 12345
    case: Case = helpers.add_case(
        store=status_db, data_analysis=Workflow.BALSAMIC, ticket=str(ticket_id)
    )

    # GIVEN an order associated with the case
    order: Order = helpers.add_order(
        store=status_db, ticket_id=ticket_id, customer_id=case.customer_id
    )
    status_db.link_case_to_order(order_id=order.id, case_id=case.id)

    # GIVEN a sample associated with the case
    sample: Sample = helpers.add_sample(
        store=status_db, last_sequenced_at=datetime.now(), application_type=AnalysisType.WES
    )
    helpers.relate_samples(base_store=status_db, case=case, samples=[sample])

    bed_name = "balsamic_integration_test_bed"
    helpers.ensure_bed_version(store=status_db, bed_name=bed_name)

    # GIVEN that a sub process can be started and run successfully
    subprocess_mock = mocker.patch.object(commands, "subprocess")
    subprocess_mock.run = Mock(
        return_value=create_autospec(
            CompletedProcess, returncode=EXIT_SUCCESS, stdout=b"", stderr=b""
        )
    )

    expect_lims_sample_request(lims_server=httpserver, sample=sample, bed_name=bed_name)

    # WHEN running balsamic config-case
    result: Result = cli_runner.invoke(
        base,
        [
            "--config",
            cg_config_file.as_posix(),
            "workflow",
            "balsamic",
            "config-case",
            case.internal_id,
        ],
        catch_exceptions=False,
    )

    assert result.exception is None
    # Move this assertion to the test above and remove this test?
    subprocess_mock.run.assert_called_once_with(
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
        "--exome "
        f"--sentieon-install-dir {test_root_dir}/balsamic_sention_licence_path "
        f"--sentieon-license localhost "
        f"--tumor-sample-name {sample.internal_id}",
        check=False,
        shell=True,
        stderr=ANY,
        stdout=ANY,
    )


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
