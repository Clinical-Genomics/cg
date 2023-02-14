"""Tests for BALSAMIC analysis"""
import logging
from pathlib import Path
from typing import Dict

import pytest
from _pytest.logging import LogCaptureFixture

from cg.constants.constants import SampleType
from cg.constants.observations import ObservationsFileWildcards
from cg.constants.sequencing import Variants
from cg.constants.subject import Gender
from cg.exc import BalsamicStartError

from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.cg_config import CGConfig


def test_get_verified_gender():
    """Tests gender extraction from a sample dictionary"""

    # GIVEN a sample object
    sample_obj = {
        "ACC0000A0": {"gender": "female"},
        "ACC0000A1": {"gender": "female"},
    }

    # WHEN extracting the gender
    retrieved_gender: Gender = BalsamicAnalysisAPI.get_verified_gender(sample_obj)

    # THEN gender must match the expected one
    assert retrieved_gender == "female"


def test_get_verified_gender_error():
    """Tests gender extraction from a sample dictionary when two different gender has been provided"""

    # GIVEN a sample object with different genders
    sample_obj = {
        "ACC0000A0": {"gender": "male"},
        "ACC0000A1": {"gender": "female"},
    }

    # WHEN extracting the gender
    with pytest.raises(BalsamicStartError):
        BalsamicAnalysisAPI.get_verified_gender(sample_obj)


def test_get_verified_gender_unknown(caplog):
    """Tests gender extraction from a sample dictionary when the gender is unknown"""

    # GIVEN a sample object with different genders
    sample_obj = {
        "ACC0000A0": {"gender": "unknown"},
        "ACC0000A1": {"gender": "unknown"},
    }

    # WHEN extracting the gender
    retrieved_gender: Gender = BalsamicAnalysisAPI.get_verified_gender(sample_obj)

    # THEN gender must match the expected one
    assert retrieved_gender == Gender.FEMALE
    assert f"The provided gender is unknown, setting {Gender.FEMALE} as the default" in caplog.text


def test_get_verified_pon():
    """Tests PON verification"""

    # GIVEN specific panel bed and PON files
    panel_bed = "/path/gmcksolid_4.1_hg19_design.bed"
    pon_cnn = "/path/PON/gmcksolid_4.1_hg19_design_CNVkit_PON_reference_v2.cnn"
    invalid_pon_cnn = "/path/PON/gmssolid_15.2_hg19_design_CNVkit_PON_reference_v2.cnn"

    # WHEN validating the PON
    validated_pon: str = BalsamicAnalysisAPI.get_verified_pon(None, panel_bed, pon_cnn)

    # THEN the PON verification should be performed successfully
    assert pon_cnn == validated_pon
    with pytest.raises(BalsamicStartError):
        BalsamicAnalysisAPI.get_verified_pon(None, panel_bed, invalid_pon_cnn)


def test_get_latest_file_by_pattern(
    cg_context: CGConfig, observations_dir: Path, observations_somatic_snv_file_path: Path
):
    """Test latest observations extraction."""

    # GIVEN a Loqusdb temporary directory and a cancer SNV file wildcard
    balsamic_analysis_api: BalsamicAnalysisAPI = BalsamicAnalysisAPI(cg_context)

    # WHEN getting the latest observations file
    observation: str = balsamic_analysis_api.get_latest_file_by_pattern(
        directory=observations_dir, pattern=ObservationsFileWildcards.CANCER_SOMATIC_SNV
    )

    # THEN the extracted observation should match the latest file
    assert observation == observations_somatic_snv_file_path.as_posix()


def test_get_parsed_observation_file_paths_no_args(
    cg_context: CGConfig,
    observations_dir: Path,
    observations_clinical_sv_file_path: Path,
    observations_somatic_snv_file_path: Path,
    outdated_observations_somatic_snv_file_path: Path,
):
    """Test verified observations extraction with no arguments."""

    # GIVEN a Loqusdb temporary directory
    balsamic_analysis_api: BalsamicAnalysisAPI = BalsamicAnalysisAPI(cg_context)
    balsamic_analysis_api.loqusdb_path = observations_dir

    # WHEN getting the latest observations arguments dictionary
    args: dict = balsamic_analysis_api.get_parsed_observation_file_paths(None)

    # THEN only the created observations files should be returned
    assert args[ObservationsFileWildcards.CLINICAL_SNV] is None
    assert (
        args[ObservationsFileWildcards.CLINICAL_SV] == observations_clinical_sv_file_path.as_posix()
    )
    assert args[ObservationsFileWildcards.CANCER_ALL_SNV] is None
    assert (
        args[ObservationsFileWildcards.CANCER_SOMATIC_SNV]
        == observations_somatic_snv_file_path.as_posix()
    )
    assert (
        outdated_observations_somatic_snv_file_path.as_posix()
        not in args[ObservationsFileWildcards.CANCER_SOMATIC_SNV]
    )
    assert args[ObservationsFileWildcards.CANCER_SOMATIC_SV] is None


def test_get_parsed_observation_file_paths_overwrite_input(
    cg_context: CGConfig,
    observations_dir: Path,
    observations_clinical_snv_file_path: Path,
    custom_observations_clinical_snv_file_path: Path,
):
    """Test verified observations extraction when providing a non default observation file."""

    # GIVEN a Loqusdb temporary directory and a custom Loqusdb file
    balsamic_analysis_api: BalsamicAnalysisAPI = BalsamicAnalysisAPI(cg_context)
    balsamic_analysis_api.loqusdb_path = observations_dir

    # WHEN getting the latest observations dictionary
    args: dict = balsamic_analysis_api.get_parsed_observation_file_paths(
        [custom_observations_clinical_snv_file_path.as_posix()]
    )

    # THEN the default file should be overwritten by the custom file
    assert (
        observations_clinical_snv_file_path.as_posix()
        not in args[ObservationsFileWildcards.CLINICAL_SNV]
    )
    assert (
        args[ObservationsFileWildcards.CLINICAL_SNV]
        == custom_observations_clinical_snv_file_path.as_posix()
    )


def test_get_swegen_verified_path(
    cg_context: CGConfig, swegen_dir: Path, swegen_snv_reference: Path
):
    """Test verified SweGen path return."""

    # GIVEN A SNV variants pattern and a BALSAMIC analysis API
    balsamic_analysis_api: BalsamicAnalysisAPI = BalsamicAnalysisAPI(cg_context)
    balsamic_analysis_api.swegen_path = swegen_dir

    # WHEN obtaining the latest file by pattern
    swegen_file: str = balsamic_analysis_api.get_swegen_verified_path(Variants.SNV)

    # THEN the returned file should match the SweGen SNV reference
    assert swegen_file == swegen_snv_reference.as_posix()
