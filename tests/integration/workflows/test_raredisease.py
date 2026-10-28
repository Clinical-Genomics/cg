from collections.abc import Callable
from pathlib import Path
from unittest.mock import Mock

import pytest
from click.testing import CliRunner, Result
from housekeeper.store.store import Store as HousekeeperStore
from pytest_httpserver import HTTPServer
from pytest_mock import MockerFixture

from cg.cli.base import base
from cg.constants.constants import Workflow
from cg.constants.priority import PriorityTerms
from cg.constants.tb import AnalysisType
from cg.store.models import Case, Sample
from cg.store.store import Store
from cg.utils import commands
from tests.integration.utils import (
    IntegrationTestPaths,
    copy_integration_test_file,
    create_empty_file,
    create_integration_test_sample_fastq_files,
    expect_lims_sample_request,
)
from tests.store_helpers import StoreHelpers


@pytest.fixture(autouse=True)
def current_workflow() -> Workflow:
    return Workflow.RAREDISEASE


@pytest.fixture(autouse=True)
def mocked_commands_and_outputs(
    scout_export_manged_variants_stdout: bytes, scout_export_panel_stdout: bytes
) -> dict[str, bytes]:
    return {
        "/scout_38/binary --config /scout_38/config export panel": scout_export_panel_stdout,
        "/scout_38/binary --config /scout_38/config export managed": scout_export_manged_variants_stdout,
    }


@pytest.fixture
def raredisease_wgs_sample(
    housekeeper_db: HousekeeperStore, status_db: Store, test_run_paths: IntegrationTestPaths
) -> Sample:
    return create_integration_test_sample_fastq_files(
        application_type=AnalysisType.WGS,
        flow_cell_id="raredisease_wgs_flow_cell",
        housekeeper_db=housekeeper_db,
        status_db=status_db,
        test_run_paths=test_run_paths,
    )


@pytest.fixture
def raredisease_express_case(
    helpers: StoreHelpers, raredisease_wgs_sample: Sample, status_db: Store
) -> Case:
    case: Case = helpers.add_case(
        store=status_db, data_analysis=Workflow.RAREDISEASE, priority=PriorityTerms.EXPRESS
    )
    helpers.relate_samples(base_store=status_db, case=case, samples=[raredisease_wgs_sample])
    return case


@pytest.fixture
def case_directory(raredisease_express_case: Case, test_run_paths: IntegrationTestPaths) -> Path:
    return Path(
        test_run_paths.test_root_dir,
        "raredisease_root_path",
        raredisease_express_case.internal_id,
    )


@pytest.fixture
def expected_config_file_contents() -> str:
    return """process.clusterOptions = "-A raredisease_slurm_account --qos=express"

// For Nextflow version 24.04.0 and above
params {
    config_profile_description = 'Platform test file'
    config_profile_contact = 'Clinical Genomics, Stockholm'
    config_profile_url = 'https://github.com/Clinical-Genomics'
}

// Slurm as executor and slurm options
executor {
    name = 'slurm'
    pollInterval = '2 min'
    queueStatInterval = '5 min'
    submitRateLimit = '2 sec'
}



"""


@pytest.fixture
def expected_params_file_contents(
    case_directory: Path, raredisease_express_case: Case, test_run_paths: IntegrationTestPaths
) -> str:
    case_id: str = raredisease_express_case.internal_id
    test_root_dir: Path = test_run_paths.test_root_dir
    return f"""input: "{case_directory}/{case_id}_samplesheet.csv"
outdir: "{case_directory}"
analysis_type: "wgs"
manta_config: "{test_root_dir}/express_manta_config.ini"
sample_id_map: "{case_directory}/{case_id}_customer_internal_mapping.csv"
skip_tools: "germlinecnvcaller"
target_bed: "{test_root_dir}/raredisease_references_directory/twistexomecomprehensive_10.2_hg38_design.bed"
vcfanno_extra_resources: "{case_directory}/managed_variants.vcf"
vep_filters_scout_fmt: "{case_directory}/gene_panels.bed"
verifybamid_svd_bed: "{test_root_dir}/raredisease/wgs/file.bed"
verifybamid_svd_mu: "{test_root_dir}/raredisease/wgs/file.mu"
verifybamid_svd_ud: "{test_root_dir}/raredisease/wgs/file.UD"
local_genomes: "/raredisease/references"
genome: "GRCh38"
fasta: "/raredisease/references/grch38_homo_sapiens_-gencode_pri-.fasta"
"""


@pytest.fixture
def expected_samplesheet_contents(
    raredisease_express_case: Case,
    raredisease_wgs_sample: Sample,
    test_run_paths: IntegrationTestPaths,
) -> str:
    case_id: str = raredisease_express_case.internal_id
    sample_id: str = raredisease_wgs_sample.internal_id
    fastq_directory = Path(test_run_paths.test_root_dir, "fastq_files")
    return f"""sample,lane,fastq_1,fastq_2,sex,phenotype,paternal_id,maternal_id,case_id
{sample_id},1,{fastq_directory}/{sample_id}.fastq.gz,{fastq_directory}/{sample_id}2.fastq.gz,2,0,,,{case_id}
"""


@pytest.mark.xdist_group(name="integration")
@pytest.mark.integration
def test_config_case_raredisease_wgs_express(
    case_directory: Path,
    expected_config_file_contents: str,
    expected_params_file_contents: str,
    expected_samplesheet_contents: str,
    httpserver: HTTPServer,
    mock_run_commands: Callable,
    raredisease_express_case: Case,
    raredisease_wgs_sample: Sample,
    scout_export_manged_variants_stdout: bytes,
    scout_export_panel_stdout: bytes,
    test_run_paths: IntegrationTestPaths,
    mocker: MockerFixture,
):
    """Test a successful run of the command 'cg workflow raredisease config-case'
    for an express case with one WGS sample."""
    cli_runner = CliRunner()

    # GIVEN an express case with a WGS sample, with:
    #  - flow cell and sequencing run stored in StatusDB
    #  - a pair of gzipped-fastq files on disk
    #  - a bundle associated with the fastq files in Housekeeper
    case_id: str = raredisease_express_case.internal_id

    # GIVEN a config file with valid database URIs and directories
    cg_config_path: Path = test_run_paths.cg_config_file

    # GIVEN the necessary configuration files exist on disk
    test_root_dir: Path = test_run_paths.test_root_dir
    copy_integration_test_file(
        from_path=Path("tests/integration/config/raredisease-params.yaml"),
        to_path=Path(test_root_dir, "raredisease_params.yaml"),
    )
    copy_integration_test_file(
        from_path=Path("tests/integration/config/platform.config"),
        to_path=Path(test_root_dir, "platform.config"),
    )
    create_empty_file(Path(test_root_dir, "raredisease_config.config"))
    create_empty_file(Path(test_root_dir, "raredisease_resources.config"))
    create_empty_file(Path(test_root_dir, "ghxx_rd_rank_model_snvs.ini"))
    create_empty_file(Path(test_root_dir, "ghxx_rd_rank_model_svs.ini"))
    create_empty_file(Path(test_root_dir, "variant_catalog.json"))

    # GIVEN that LIMS has no capture kit for the sample
    expect_lims_sample_request(lims_server=httpserver, sample=raredisease_wgs_sample, bed_name="NA")
    httpserver.expect_request("/lims/api/v2/artifacts").respond_with_data(
        '<art:artifacts xmlns:art="http://genologics.com/ri/artifact"/>',
        content_type="application/xml",
    )

    # GIVEN that the Scout commands return exported panel data and managed variants
    subprocess_mock = mocker.patch.object(commands, "subprocess")
    subprocess_mock.run = Mock(side_effect=mock_run_commands)

    # WHEN running raredisease config-case
    result: Result = cli_runner.invoke(
        base,
        [
            "--config",
            cg_config_path.as_posix(),
            "workflow",
            "raredisease",
            "config-case",
            case_id,
        ],
        catch_exceptions=False,
    )

    # THEN a successful exit code is returned
    assert result.exit_code == 0

    # THEN the following files have been created with the correct contents:
    # - CASE_ID_nextflow_config.json
    # - CASE_ID_params_file.yaml
    # - CASE_ID_samplesheet.csv
    # - CASE_ID_customer_internal_mapping.csv
    # - gene_panels.bed
    # - managed_variants.vcf
    assert (
        Path(case_directory, f"{case_id}_nextflow_config.json").open().read()
        == expected_config_file_contents
    )

    assert (
        Path(case_directory, f"{case_id}_params_file.yaml").open().read()
        == expected_params_file_contents
    )

    assert (
        Path(case_directory, f"{case_id}_samplesheet.csv").open().read()
        == expected_samplesheet_contents
    )

    assert (
        Path(case_directory, f"{case_id}_customer_internal_mapping.csv").open().read()
        == f"customer_id,internal_id\n{raredisease_wgs_sample.name},{raredisease_wgs_sample.internal_id}\n"
    )

    assert (
        Path(case_directory, "gene_panels.bed").open().read() == scout_export_panel_stdout.decode()
    )

    assert (
        Path(case_directory, "managed_variants.vcf").open().read()
        == scout_export_manged_variants_stdout.decode()
    )

    # THEN the rank model files and the variant catalog have been copied into the case directory
    assert Path(case_directory, "ghxx_rd_rank_model_snvs.ini").is_file()
    assert Path(case_directory, "ghxx_rd_rank_model_svs.ini").is_file()
    assert Path(case_directory, "variant_catalog.json").is_file()
