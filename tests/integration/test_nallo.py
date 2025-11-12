from collections.abc import Callable
from pathlib import Path
from unittest.mock import Mock

import pytest
from click.testing import CliRunner, Result
from housekeeper.store.store import Store as HousekeeperStore
from pytest_httpserver import HTTPServer
from pytest_mock import MockerFixture

from cg.cli.base import base
from cg.constants.constants import CaseActions, Workflow
from cg.constants.tb import AnalysisType
from cg.store.models import Case, Order, Sample
from cg.store.store import Store
from cg.utils import commands
from tests.integration.utils import (
    IntegrationTestPaths,
    copy_integration_test_file,
    create_empty_file,
    create_integration_test_sample_bam_files,
    expect_to_add_pending_analysis_to_trailblazer,
    expect_to_get_latest_analysis_with_empty_response_from_trailblazer,
)
from tests.store_helpers import StoreHelpers


@pytest.fixture(autouse=True)
def current_workflow() -> Workflow:
    return Workflow.NALLO


@pytest.fixture
def new_tower_id() -> str:
    return "1uxZE9JM7Tl58r"


@pytest.fixture(autouse=True)
def mocked_commands_and_outputs(
    new_tower_id: str, scout_export_manged_variants_stdout: bytes, scout_export_panel_stdout: bytes
) -> dict[str, bytes]:
    return {
        "/scout_38/binary --config /scout_38/config export panel": scout_export_panel_stdout,
        "/scout_38/binary --config /scout_38/config export managed": scout_export_manged_variants_stdout,
        "tower_binary_path launch": f"Workflow {new_tower_id} submitted at [<WORKSPACE>] workspace.".encode(),
    }


@pytest.fixture
def ticket_id() -> int:
    return 12345


@pytest.fixture
def nallo_case(helpers: StoreHelpers, status_db: Store, ticket_id: int) -> Case:
    return helpers.add_case(store=status_db, data_analysis=Workflow.NALLO, ticket=str(ticket_id))


@pytest.fixture
def nallo_sample(
    housekeeper_db: HousekeeperStore, status_db: Store, test_run_paths: IntegrationTestPaths
) -> Sample:
    return create_integration_test_sample_bam_files(
        status_db=status_db, housekeeper_db=housekeeper_db, test_run_paths=test_run_paths
    )


@pytest.fixture
def expected_config_file_contents() -> str:
    return """process.clusterOptions = "-A nallo_slurm_account --qos=normal"

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
def expected_params_file_contents(nallo_case: Case, test_run_paths: IntegrationTestPaths) -> str:
    return f"""input: "{test_run_paths.test_root_dir}/nallo_root_path/{nallo_case.internal_id}/{nallo_case.internal_id}_samplesheet.csv"
outdir: "{test_run_paths.test_root_dir}/nallo_root_path/{nallo_case.internal_id}"
filter_variants_hgnc_ids: "{test_run_paths.test_root_dir}/nallo_root_path/{nallo_case.internal_id}/gene_panels.tsv"
references: "/nallo/references/v0.3.1"
resources: "/nallo/resources"
alignment_processes: 64
cadd_prescored_indels: "/nallo/references/v0.3.1/prescored"
cadd_resources: "/nallo/references/v0.3.1/CADD-scripts/data/annotations"
echtvar_snv_databases: "/nallo/resources/nallo_v1.0_prod_snv_databases.yaml"
fasta: "/nallo/references/v0.3.1/GRCh38_GIABv3_no_alt_analysis_set_maskedGRC_decoys_MAP2K3_KMT2C_KCNJ18.fasta"
filter_snvs_expression: "-e \'colorsdb_af > 0.05 || gnomad_af > 0.05 || Frq > 0.3\'"
filter_svs_expression: "-e \'colorsdb_af > 0.05 || gnomad_af > 0.05 || clinical_genomics_loqusFrq > 0.3\'"
genmod_reduced_penetrance: "/nallo/references/v0.3.1/grch38_reduced_penetrance_-v1.0-.tsv"
genmod_score_config_snvs: "/nallo/references/v0.3.1/grch38_rank_model_snvs_-v1.0-.ini"
genmod_score_config_svs: "/nallo/references/v0.3.1/grch38_rank_model_svs_-v1.0-.ini"
hificnv_excluded_regions: "/nallo/references/v0.3.1/grch38_hificnv_excluded_regions_common_50_-v1.0-.bed.gz"
hificnv_expected_xx_cn: "/nallo/references/v0.3.1/grch38_hificnv_expected_copynumer_xx_-v1.0-.bed"
hificnv_expected_xy_cn: "/nallo/references/v0.3.1/grch38_hificnv_expected_copynumer_xy_-v1.0-.bed"
par_regions: "/nallo/references/v0.3.1/grch38_par_-v1.0-.bed"
publish_unannotated_family_svs: True
skip_genome_assembly: True
snv_calling_processes: 20
somalier_sites: "/nallo/references/v0.3.1/sites.hg38.vcf.gz"
stranger_repeat_catalog: "/nallo/references/v0.3.1/grch38_variant_catalog_stranger.json"
svdb_sv_databases: "/nallo/resources/nallo_v1.0_prod_sv_databases.yaml"
sv_caller: "sniffles"
target_regions: "/nallo/references/v0.3.1/grch38_chromosomes_split_at_centromeres_-v1.0-.bed"
str_bed: "/nallo/references/v0.3.1/grch38_trgt_pathogenic_repeats.bed"
variant_consequences_snvs: "/nallo/references/v0.3.1/grch38_variant_consequences_-v1.0-.txt"
variant_consequences_svs: "/nallo/references/v0.3.1/grch38_variant_consequences_-v1.0-.txt"
vep_cache: "/nallo/references/v0.3.1/vep_cache"
vep_plugin_files: "/nallo/resources/nallo_v1.0_prod_vep_files.yaml"
"""


@pytest.fixture
def expected_samplesheet_contents(
    nallo_case: Case, nallo_sample: Sample, test_run_paths: IntegrationTestPaths
) -> str:
    return f"""project,sample,file,family_id,paternal_id,maternal_id,sex,phenotype
{nallo_case.internal_id},{nallo_sample.internal_id},{test_run_paths.test_root_dir}/file1.bam,{nallo_case.internal_id},0,0,2,0
{nallo_case.internal_id},{nallo_sample.internal_id},{test_run_paths.test_root_dir}/file2.bam,{nallo_case.internal_id},0,0,2,0
"""


@pytest.fixture
def expected_tower_ids_contents(nallo_case: Case, new_tower_id: str) -> str:
    return f"""---
{nallo_case.internal_id}:
- {new_tower_id}
"""


@pytest.mark.xdist_group(name="integration")
@pytest.mark.integration
def test_start_available_nallo(
    expected_config_file_contents: str,
    expected_params_file_contents: str,
    expected_samplesheet_contents: str,
    expected_tower_ids_contents: str,
    helpers: StoreHelpers,
    httpserver: HTTPServer,
    scout_export_panel_stdout: bytes,
    status_db: Store,
    test_run_paths: IntegrationTestPaths,
    ticket_id: int,
    mock_run_commands: Callable,
    nallo_case: Case,
    nallo_sample: Sample,
    new_tower_id: str,
    mocker: MockerFixture,
):
    """Test a successful run of the command 'cg workflow nallo start-available'
    with one case to be analysed that has not been analysed before."""
    cli_runner = CliRunner()

    # GIVEN a case
    # GIVEN a sample
    # GIVEN a config file with valid database URIs and directories
    config_path: Path = test_run_paths.cg_config_file

    # GIVEN the necessary configured directories exist
    test_root_dir = test_run_paths.test_root_dir
    copy_integration_test_file(
        from_path=Path("tests/integration/config/nallo-params.yaml"),
        to_path=Path(test_root_dir, "nallo_params.yaml"),
    )
    copy_integration_test_file(
        from_path=Path("tests/integration/config/platform.config"),
        to_path=Path(test_root_dir, "platform.config"),
    )
    create_empty_file(Path(test_root_dir, "nallo_config.config"))
    create_empty_file(Path(test_root_dir, "nallo_resources.config"))

    # GIVEN an order associated with the case
    order: Order = helpers.add_order(
        store=status_db, ticket_id=ticket_id, customer_id=nallo_case.customer_id
    )
    status_db.link_case_to_order(order_id=order.id, case_id=nallo_case.id)

    # GIVEN a sample associated with the case, with:
    #  - flow cell and sequencing run stored in StatusDB
    #  - a gzipped-fastq file on disk
    #  - a bundle associated with the fastq file in Housekeeper
    sample: Sample = nallo_sample
    helpers.relate_samples(base_store=status_db, case=nallo_case, samples=[sample])

    # GIVEN that the Scout command returns exported panel data
    subprocess_mock = mocker.patch.object(commands, "subprocess")
    subprocess_mock.run = Mock(side_effect=mock_run_commands)

    # GIVEN the Trailblazer API returns no ongoing analysis for the case
    expect_to_get_latest_analysis_with_empty_response_from_trailblazer(
        trailblazer_server=httpserver, case_id=nallo_case.internal_id
    )

    # GIVEN a new pending analysis can be added to the Trailblazer API
    # case_path = Path(mip_dna_path, "cases", case.internal_id)
    expect_to_add_pending_analysis_to_trailblazer(
        analysis_type=AnalysisType.WGS,
        out_dir=Path(test_root_dir, "nallo_root_path", nallo_case.internal_id),
        case=nallo_case,
        config_path=Path(
            test_root_dir, "nallo_root_path", nallo_case.internal_id, "tower_ids.yaml"
        ),
        ticket_id=ticket_id,
        trailblazer_server=httpserver,
        tower_workflow_id=new_tower_id,
        workflow=Workflow.NALLO,
        workflow_manager="nf_tower",
    )

    # WHEN running mip-dna start-available
    result: Result = cli_runner.invoke(
        base,
        [
            "--config",
            config_path.as_posix(),
            "workflow",
            "nallo",
            "start-available",
        ],
        catch_exceptions=False,
    )

    # THEN a successful exit code is returned
    assert result.exit_code == 0

    # THEN the analysis should be started in the correct way
    _first_call = subprocess_mock.mock_calls[0]
    second_call = subprocess_mock.mock_calls[1]

    expected_run_command: list[str] = [
        f"{test_root_dir}/tower_binary_path",
        "launch",
        "--work-dir",
        f"{test_root_dir}/nallo_root_path/{nallo_case.internal_id}/work",
        "--profile",
        "nallo_profile",
        "--params-file",
        f"{test_root_dir}/nallo_root_path/{nallo_case.internal_id}/{nallo_case.internal_id}_params_file.yaml",
        "--config",
        f"{test_root_dir}/nallo_root_path/{nallo_case.internal_id}/{nallo_case.internal_id}_nextflow_config.json",
        "--name",
        nallo_case.internal_id,
        "--revision",
        "nallo_revision",
        "--compute-env",
        "nallo_compute_env-normal",
        "nallo_tower_workflow",
    ]
    assert second_call.args[0] == expected_run_command

    # THEN an analysis has been created for the case
    assert len(nallo_case.analyses) == 1

    # THEN the case action is set to running
    status_db.session.refresh(nallo_case)
    assert nallo_case.action == CaseActions.RUNNING

    # THEN the following files have been created with the correct contents:
    # - CASE_ID_nextflow_config.json
    # - CASE_ID_params_file.yaml
    # - CASE_ID_samplesheet.csv
    # - gene_panels.tsv
    # - tower_ids.yaml

    case_directory = Path(test_root_dir, "nallo_root_path", nallo_case.internal_id)

    assert (
        Path(case_directory, f"{nallo_case.internal_id}_nextflow_config.json").open().read()
        == expected_config_file_contents
    )

    assert (
        Path(case_directory, f"{nallo_case.internal_id}_params_file.yaml").open().read()
        == expected_params_file_contents
    )

    assert (
        Path(case_directory, f"{nallo_case.internal_id}_samplesheet.csv").open().read()
        == expected_samplesheet_contents
    )

    assert Path(
        case_directory, "gene_panels.tsv"
    ).open().read() == scout_export_panel_stdout.decode().removesuffix("\n")

    assert Path(case_directory, "tower_ids.yaml").open().read() == expected_tower_ids_contents
