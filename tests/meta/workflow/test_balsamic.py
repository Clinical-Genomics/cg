"""Tests for BALSAMIC analysis"""

import pytest

from cg.constants.loqus_upload import ObservationFileWildcards
from cg.constants.subject import Gender
from cg.exc import BalsamicStartError

from cg.meta.workflow.balsamic import BalsamicAnalysisAPI


def test_get_verified_gender():
    """Tests gender extraction from a sample dictionary"""

    # GIVEN a sample object
    sample_obj = {
        "ACC0000A0": {"gender": "female"},
        "ACC0000A1": {"gender": "female"},
    }

    # WHEN extracting the gender
    retrieved_gender = BalsamicAnalysisAPI.get_verified_gender(sample_obj)

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
    retrieved_gender = BalsamicAnalysisAPI.get_verified_gender(sample_obj)

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
    validated_pon = BalsamicAnalysisAPI.get_verified_pon(None, panel_bed, pon_cnn)

    # THEN the PON verification should be performed successfully
    assert pon_cnn == validated_pon
    with pytest.raises(BalsamicStartError):
        BalsamicAnalysisAPI.get_verified_pon(None, panel_bed, invalid_pon_cnn)


def test_get_latest_observations_export_file(cg_context, observations_dir, observations_files_path):
    """Test latest observations extraction."""

    # GIVEN a Loqusdb temporary directory and a file wildcard
    balsamic_analysis_api = BalsamicAnalysisAPI(cg_context)
    balsamic_analysis_api.loqusdb_path = observations_dir
    wildcard = ObservationFileWildcards.CANCER_SOMATIC_SNV

    # WHEN getting the latest observations file
    observation = balsamic_analysis_api.get_latest_observations_export_file(wildcard)

    # THEN the extracted observation should match the latest file
    assert observation == str(observations_files_path[0])


def test_get_parsed_observation_file_paths_no_args(
    cg_context, observations_dir, observations_files_path
):
    """Test verified observations extraction with no arguments."""

    # GIVEN a Loqusdb temporary directory
    balsamic_analysis_api = BalsamicAnalysisAPI(cg_context)
    balsamic_analysis_api.loqusdb_path = observations_dir

    # GIVEN the expected output dictionary
    expected_args = {
        "clinical-snv-observations": None,
        "clinical-sv-observations": str(observations_files_path[2]),
        "cancer-all-snv-observations": None,
        "cancer-somatic-snv-observations": str(observations_files_path[0]),
        "cancer-somatic-sv-observations": None,
    }

    # WHEN getting the latest observations dictionary
    args: dict = balsamic_analysis_api.get_parsed_observation_file_paths(None)

    # THEN the extracted observation arguments should match the expected one
    assert args == expected_args


def test_get_parsed_observation_file_paths_overwrite_input(
    cg_context, observations_dir, observations_files_path
):
    """Test verified observations extraction when providing a non default observation file."""

    # GIVEN a Loqusdb temporary directory and a list of custom Loqusdb files
    balsamic_analysis_api = BalsamicAnalysisAPI(cg_context)
    balsamic_analysis_api.loqusdb_path = observations_dir
    loqusdb_files = [
        "/test/path/clinical_snv_export-19990101-.vcf",
        "/test/path/cancer_somatic_snv_export-19990101-.vcf",
    ]

    # GIVEN the expected output dictionary
    expected_args = {
        "clinical-snv-observations": loqusdb_files[0],
        "clinical-sv-observations": str(observations_files_path[2]),
        "cancer-all-snv-observations": None,
        "cancer-somatic-snv-observations": loqusdb_files[1],
        "cancer-somatic-sv-observations": None,
    }

    # WHEN getting the latest observations dictionary
    args: dict = balsamic_analysis_api.get_parsed_observation_file_paths(loqusdb_files)

    # THEN the extracted observation arguments should match the expected one
    assert args == expected_args
