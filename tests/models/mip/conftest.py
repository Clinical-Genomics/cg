from pathlib import Path

import pytest

from cg.constants.priority import SlurmQos
from cg.models.mip.mip_config import MipBaseConfig
from cg.models.mip.mip_sample_info import MipBaseSampleInfo


@pytest.fixture(name="mip_case_config_dna")
def fixture_mip_case_config_dna(fixtures_dir) -> Path:
    """Return path to MIP DNA case_config.yaml"""
    return Path(fixtures_dir, "apps", "mip", "dna", "store", "case_config.yaml")


@pytest.fixture(name="mip_analysis_config_dna_raw")
def fixture_mip_analysis_config_dna_raw() -> dict:
    """Raw MIP DNA analysis config"""
    return {
        "analysis_type": {"sample_id": "wgs"},
        "case_id": "yellowhog",
        "config_file_analysis": "a_config_path",
        "email": "someone@somewhere.com",
        "family_id": "a_family_id",
        "dry_run_all": False,
        "log_file": "a_log_path",
        "outdata_dir": "tests/fixtures/apps/mip/dna/store",
        "sample_ids": ["sample_id"],
        "sample_info_file": "tests/fixtures/apps/mip/dna/store/case_qc_sample_info.yaml",
        "slurm_quality_of_service": SlurmQos.LOW,
        "store_file": "tests/fixtures/apps/mip/dna/store/case_id_deliverables.yaml",
    }


@pytest.fixture(name="mip_analysis_config_dna")
def fixture_mip_analysis_config_dna(mip_analysis_config_dna_raw: dict) -> MipBaseConfig:
    return MipBaseConfig(**mip_analysis_config_dna_raw)


@pytest.fixture(name="sample_info_dna_raw")
def fixture_sample_info_dna_raw() -> dict:
    """Raw sample_info fixture"""
    return {
        "analysisrunstatus": "finished",
        "analysis_date": "2021-05-05T16:16:01",
        "case_id": "yellowhog",
        "family_id": "a_family_id",
        "human_genome_build": {"version": 37, "source": "grch"},
        "mip_version": "v9.0.0",
        "recipe": {
            "genmod": {
                "rank_model": {"version": "v1.0"},
            },
            "sv_genmod": {
                "sv_rank_model": {"version": "v1.2.0"},
            },
        },
    }


@pytest.fixture(name="sample_info_dna")
def fixture_sample_info_dna(sample_info_dna_raw: dict) -> MipBaseSampleInfo:
    return MipBaseSampleInfo(**sample_info_dna_raw)


@pytest.fixture(name="mip_metrics_deliverables_raw")
def fixture_mip_metrics_deliverables_raw() -> dict:
    """Raw MIP metrics deliverables"""
    return {
        "metrics": [
            {
                "id": "an_id",
                "input": "file_1",
                "name": "raw_total_sequences",
                "step": "bamstats",
                "value": "296436536",
            },
            {
                "id": "an_id",
                "input": "file_2",
                "name": "raw_total_sequences",
                "step": "bamstats",
                "value": "287527252",
            },
            {
                "id": "an_id",
                "input": "file_1",
                "name": "reads_mapped",
                "step": "bamstats",
                "value": "295720636",
            },
            {
                "id": "an_id",
                "input": "file_2",
                "name": "reads_mapped",
                "step": "bamstats",
                "value": "286811812",
            },
            {
                "id": "another_id",
                "input": "file_1",
                "name": "raw_total_sequences",
                "step": "bamstats",
                "value": "286214720",
            },
            {
                "id": "another_id",
                "input": "file_2",
                "name": "raw_total_sequences",
                "step": "bamstats",
                "value": "284211662",
            },
            {
                "id": "another_id",
                "input": "file_1",
                "name": "reads_mapped",
                "step": "bamstats",
                "value": "285581150",
            },
            {
                "id": "another_id",
                "input": "file_2",
                "name": "reads_mapped",
                "step": "bamstats",
                "value": "283570947",
            },
            {
                "id": "an_id",
                "input": "some_input",
                "name": "MEAN_INSERT_SIZE",
                "step": "collectmultiplemetricsinsertsize",
                "value": "422.245916",
            },
            {
                "id": "another_id",
                "input": "some_input",
                "name": "MEAN_INSERT_SIZE",
                "step": "collectmultiplemetricsinsertsize",
                "value": "399.51625",
            },
            {
                "id": "an_id",
                "input": "some_input",
                "name": "gender",
                "step": "chanjo_sexcheck",
                "value": "female",
            },
            {
                "id": "another_id",
                "input": "some_input",
                "name": "gender",
                "step": "chanjo_sexcheck",
                "value": "male",
            },
            {
                "id": "an_id",
                "input": "some_input",
                "name": "fraction_duplicates",
                "step": "markduplicates",
                "value": "0.0748899652117993",
            },
            {
                "id": "another_id",
                "input": "some_input",
                "name": "fraction_duplicates",
                "step": "markduplicates",
                "value": "0.09",
            },
        ],
    }
