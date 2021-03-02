import shutil
from pathlib import Path

import pytest

from cg.apps.housekeeper.models import InputBundle
from cg.constants import Pipeline
from cg.meta.workflow.fluffy import FluffyAnalysisAPI
import datetime as dt


@pytest.fixture(name="config_root_dir")
def config_root_dir():
    return Path("tests/fixtures/data")


@pytest.fixture(name="database_copy_path")
def database_copy_path(tmpdir_factory):
    return tmpdir_factory.mktemp("database/")


@pytest.fixture(name="fixture_db_url")
def fixture_db_url(database_copy_path):
    new_path = shutil.copy("tests/fixtures/data/cgfixture.db", database_copy_path)
    return f"sqlite:///{new_path}"


@pytest.fixture(name="context_config")
def context_config(config_root_dir, fixture_db_url) -> dict:
    root_dir = config_root_dir.as_posix()
    return {
        "database": fixture_db_url,
        "madeline_exe": "madeline2",
        "bed_path": root_dir,
        "delivery_path": root_dir,
        "hermes": {"deploy_config": "hermes-deploy-stage.yaml", "binary_path": "hermes"},
        "fluffy": {
            "deploy_config": "fluffy-deploy-stage.yaml",
            "binary_path": "fluffy",
            "config_path": "fluffy/Config.json",
            "root_dir": root_dir,
        },
        "shipping": {"host_config": "host_config_stage.yaml", "binary_path": "shipping"},
        "housekeeper": {"database": "sqlite:///./housekeeper", "root": root_dir},
        "trailblazer": {
            "service_account": "SERVICE",
            "service_account_auth_file": "trailblazer-auth.json",
            "host": "https://trailblazer-api-stage.scilifelab.se/api/v1",
        },
        "lims": {
            "host": "https://clinical-lims-stage.scilifelab.se",
            "username": "user",
            "password": "password",
        },
        "chanjo": {"binary_path": "chanjo", "config_path": "chanjo-stage.yaml"},
        "genotype": {
            "database": "sqlite:///./genotype",
            "binary_path": "genotype",
            "config_path": "genotype-stage.yaml",
        },
        "vogue": {"binary_path": "vogue", "config_path": "vogue-stage.yaml"},
        "cgstats": {"database": "sqlite:///./cgstats", "root": root_dir},
        "scout": {
            "binary_path": "scout",
            "config_path": "scout-stage.yaml",
            "deploy_config": "scout-deploy-stage.yaml",
        },
        "loqusdb": {"binary_path": "loqusdb", "config_path": "loqusdb-stage.yaml"},
        "loqusdb-wes": {"binary_path": "loqusdb", "config_path": "loqusdb-wes-stage.yaml"},
        "balsamic": {
            "root": root_dir,
            "singularity": "BALSAMIC_release_v6.0.1.sif",
            "reference_config": "reference.json",
            "binary_path": "balsamic",
            "conda_env": "S_BALSAMIC",
            "slurm": {
                "mail_user": "test.email@scilifelab.se",
                "account": "development",
                "qos": "low",
            },
        },
        "microsalt": {
            "root": root_dir,
            "queries_path": Path(root_dir, "queries").as_posix(),
            "binary_path": "microSALT",
            "conda_env": "S_microSALT",
        },
        "mip-rd-dna": {
            "conda_env": "S_mip9.0",
            "mip_config": "mip9.0-dna-stage.yaml",
            "pipeline": "analyse rd_dna",
            "root": root_dir,
            "script": "mip",
        },
        "mip-rd-rna": {
            "conda_env": "S_mip9.0",
            "mip_config": "mip9.0-rna-stage.yaml",
            "pipeline": "analyse rd_rna",
            "root": root_dir,
            "script": "mip",
        },
        "mutacc-auto": {
            "config_path": "mutacc-auto-stage.yaml",
            "binary_path": "mutacc-auto",
            "padding": 300,
        },
        "crunchy": {
            "cram_reference": "grch37_homo_sapiens_-d5-.fasta",
            "slurm": {
                "account": "development",
                "mail_user": "magnus.mansson@scilifelab.se",
                "conda_env": "S_crunchy",
            },
        },
        "backup": {"root": {"hiseqx": "flowcells/hiseqx", "hiseqga": "RUNS/", "novaseq": "runs/"}},
    }


@pytest.fixture(scope="function")
def fluffy_case_id_existing():
    return "lovedkitten"


@pytest.fixture(scope="function")
def fluffy_case_id_non_existing():
    return "nakedmolerat"


@pytest.fixture(scope="function")
def fluffy_sample_lims_id():
    return "ACC9001A1"


@pytest.fixture(scope="function")
def fluffy_dir(tmpdir_factory):
    return tmpdir_factory.mktemp("fluffy")


@pytest.fixture(scope="function")
def fluffy_cases_dir(tmpdir_factory, fluffy_dir):
    return tmpdir_factory.mktemp("cases")


@pytest.fixture(scope="function")
def fluffy_success_output_summary(tmpdir_factory):
    output_dir = tmpdir_factory.mktemp("output")
    file_path = Path(output_dir, "summary.csv")
    file_path.touch(exist_ok=True)
    return file_path


@pytest.fixture(scope="function")
def fluffy_success_output_multiqc(tmpdir_factory):
    output_dir = tmpdir_factory.mktemp("output")
    file_path = Path(output_dir, "multiqc_report.html")
    file_path.touch(exist_ok=True)
    return file_path


@pytest.fixture(scope="function")
def fluffy_success_output_aberrations(tmpdir_factory):
    output_dir = tmpdir_factory.mktemp("output")
    file_path = Path(output_dir, "WCXpredict_aberrations.filt.bed")
    file_path.touch(exist_ok=True)
    return file_path


@pytest.fixture(scope="function")
def samplesheet_fixture_path(config_root_dir):
    fixture_path = Path(config_root_dir)
    return Path(fixture_path, "SampleSheet.csv").absolute()


@pytest.fixture(scope="function")
def fastq_file_fixture_path(config_root_dir):
    fixture_path = Path(config_root_dir, "tests/fixtures/apps/fluffy/")
    fixture_path.mkdir(parents=True, exist_ok=True)
    fixture_fastq_path = Path(fixture_path, "fluffy_fastq.fastq.gz")
    fixture_fastq_path.touch(exist_ok=True)
    return fixture_fastq_path


@pytest.fixture(scope="function")
def deliverables_yaml_fixture_path():
    return Path("tests/fixtures/apps/fluffy/deliverables.yaml")


@pytest.fixture()
def fluffy_hermes_deliverables_response_data(
    fluffy_case_id_existing,
    fluffy_sample_lims_id,
    fluffy_success_output_multiqc,
    fluffy_success_output_summary,
    fluffy_success_output_aberrations,
):
    return InputBundle(
        **{
            "files": [
                {
                    "path": fluffy_success_output_summary.as_posix(),
                    "tags": ["metrics", fluffy_case_id_existing, "nipt"],
                },
                {
                    "path": fluffy_success_output_multiqc.as_posix(),
                    "tags": ["multiqc-html", fluffy_case_id_existing, "nipt"],
                },
                {
                    "path": fluffy_success_output_aberrations.as_posix(),
                    "tags": ["wisecondor", "cnv", fluffy_sample_lims_id, "nipt"],
                },
            ],
            "created": dt.datetime.now(),
            "name": fluffy_case_id_existing,
        }
    )


@pytest.fixture(scope="function")
def fluffy_fastq_hk_bundle_data(fastq_file_fixture_path, fluffy_sample_lims_id) -> dict:
    return {
        "name": fluffy_sample_lims_id,
        "created": dt.datetime.now(),
        "version": "1.0",
        "files": [
            {"path": fastq_file_fixture_path.as_posix(), "tags": ["fastq"], "archive": False}
        ],
    }


@pytest.fixture(scope="function")
def fluffy_samplesheet_bundle_data(samplesheet_fixture_path) -> dict:
    return {
        "name": "flowcell",
        "created": dt.datetime.now(),
        "version": "1.0",
        "files": [
            {"path": str(samplesheet_fixture_path), "tags": ["samplesheet"], "archive": False}
        ],
    }


@pytest.fixture(scope="function")
def fluffy_context(
    context_config,
    helpers,
    fluffy_case_id_existing,
    fluffy_sample_lims_id,
) -> dict:
    fluffy_analysis_api = FluffyAnalysisAPI(config=context_config)
    example_fluffy_case = helpers.add_case(
        fluffy_analysis_api.status_db,
        internal_id=fluffy_case_id_existing,
        case_id=fluffy_case_id_existing,
        data_analysis=Pipeline.FLUFFY,
    )
    example_fluffy_sample = helpers.add_sample(
        fluffy_analysis_api.status_db,
        internal_id=fluffy_sample_lims_id,
        is_tumour=False,
        application_type="tgs",
        reads=100,
        sequenced_at=dt.datetime.now(),
    )
    helpers.add_flowcell(
        fluffy_analysis_api.status_db, flowcell_id="flowcell", samples=[example_fluffy_sample]
    )
    helpers.add_relationship(
        fluffy_analysis_api.status_db, case=example_fluffy_case, sample=example_fluffy_sample
    )
    return {"analysis_api": fluffy_analysis_api}
