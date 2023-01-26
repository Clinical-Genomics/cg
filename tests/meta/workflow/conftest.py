"""Fixtures for the prepare_fastq api tests."""
from typing import Dict

import pytest

from cg.constants.constants import SampleType
from cg.constants.sequencing import SequencingMethod
from cg.constants.subject import Gender

from cg.meta.compress.compress import CompressAPI
from cg.models.compression_data import CompressionData

from tests.meta.compress.conftest import fixture_compress_api, fixture_real_crunchy_api
from tests.cli.workflow.balsamic.conftest import (
    fastq_file_l_1_r_1,
    fastq_file_l_2_r_1,
    fastq_file_l_2_r_2,
    balsamic_housekeeper_dir,
)
from tests.meta.upload.scout.conftest import fixture_another_sample_id


@pytest.fixture(scope="function", name="populated_compress_spring_api")
def fixture_populated_compress_spring_api(
    compress_api: CompressAPI, only_spring_bundle: dict, helpers
) -> CompressAPI:
    """Populated compress api fixture with only spring compressed fastq."""
    helpers.ensure_hk_bundle(compress_api.hk_api, only_spring_bundle)

    return compress_api


@pytest.fixture(scope="function", name="populated_compress_api_fastq_spring")
def fixture_populated_compress_api_fastq_spring(
    compress_api: CompressAPI, spring_fastq_mix: dict, helpers
) -> CompressAPI:
    """Populated compress api fixture with both spring and fastq."""
    helpers.ensure_hk_bundle(compress_api.hk_api, spring_fastq_mix)

    return compress_api


@pytest.fixture(name="only_spring_bundle")
def fixture_only_spring_bundle() -> dict:
    """Return a dictionary with bundle info in the correct format."""
    return {
        "name": "ADM1",
        "created": "2019-12-24",
        "files": [
            {
                "path": "/path/HVCHCCCXY-l4t21_535422_S4_L004.spring",
                "archive": False,
                "tags": ["spring"],
            },
        ],
    }


@pytest.fixture(name="spring_fastq_mix")
def fixture_spring_fastq_mix(compression_object: CompressionData) -> dict:
    """Return a dictionary with bundle info including both fastq and spring files."""

    return {
        "name": "ADM1",
        "created": "2019-12-24",
        "files": [
            {
                "path": str(compression_object.spring_path),
                "archive": False,
                "tags": ["spring"],
            },
            {
                "path": str(compression_object.fastq_first),
                "archive": False,
                "tags": ["fastq"],
            },
            {
                "path": str(compression_object.fastq_second),
                "archive": False,
                "tags": ["fastq"],
            },
        ],
    }


@pytest.fixture(name="balsamic_sample_data")
def fixture_balsamic_sample_data(
    sample_id: str,
    cust_sample_id: str,
    another_sample_id: str,
    fastq_file_l_1_r_1: str,
    fastq_file_l_2_r_1: str,
    fastq_file_l_2_r_2: str,
    bed_file: str,
) -> Dict[str, dict]:
    """Balsamic sample data dictionary."""
    return {
        sample_id: {
            "gender": Gender.FEMALE,
            "tissue_type": SampleType.TUMOR,
            "concatenated_path": fastq_file_l_1_r_1,
            "application_type": SequencingMethod.TGS,
            "target_bed": bed_file,
        },
        cust_sample_id: {
            "gender": Gender.FEMALE,
            "tissue_type": SampleType.NORMAL,
            "concatenated_path": fastq_file_l_2_r_1,
            "application_type": SequencingMethod.TGS,
            "target_bed": bed_file,
        },
        another_sample_id: {
            "gender": Gender.FEMALE,
            "tissue_type": SampleType.NORMAL,
            "concatenated_path": fastq_file_l_2_r_2,
            "application_type": SequencingMethod.TGS,
            "target_bed": bed_file,
        },
    }
