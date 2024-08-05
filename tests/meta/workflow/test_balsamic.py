"""Tests for BALSAMIC analysis."""

from pathlib import Path

import pytest

from cg.constants.observations import ObservationsFileWildcards
from cg.constants.sequencing import Variants
from cg.constants.subject import Sex
from cg.exc import BalsamicStartError
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.balsamic.analysis import BalsamicAnalysis
from cg.models.cg_config import CGConfig
from tests.mocks.balsamic_analysis_mock import MockBalsamicAnalysis


def test_get_verified_sex():
    """Test sex extraction from a sample dictionary."""

    # GIVEN a sample object
    sample_obj = {
        "ACC0000A0": {"sex": "female"},
        "ACC0000A1": {"sex": "female"},
    }

    # WHEN extracting the sex
    retrieved_sex: Sex = BalsamicAnalysisAPI.get_verified_sex(sample_obj)

    # THEN sex must match the expected one
    assert retrieved_sex == "female"


def test_get_verified_sex_error():
    """Test sex extraction from a sample dictionary when two different sexes have been provided."""

    # GIVEN a sample object with different sexes
    sample_obj = {
        "ACC0000A0": {"sex": "male"},
        "ACC0000A1": {"sex": "female"},
    }

    # WHEN extracting the sex
    with pytest.raises(BalsamicStartError):
        BalsamicAnalysisAPI.get_verified_sex(sample_obj)


def test_get_verified_sex_unknown(caplog):
    """Tests sex extraction from a sample dictionary when the sex is unknown."""

    # GIVEN a sample object with different sexes
    sample_obj = {
        "ACC0000A0": {"sex": "unknown"},
        "ACC0000A1": {"sex": "unknown"},
    }

    # WHEN extracting the sex
    retrieved_sex: Sex = BalsamicAnalysisAPI.get_verified_sex(sample_obj)

    # THEN sex must match the expected one
    assert retrieved_sex == Sex.FEMALE
    assert f"The provided sex is unknown, setting {Sex.FEMALE} as the default" in caplog.text


def test_get_verified_pon():
    """Tests PON verification."""

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
    assert args[ObservationsFileWildcards.CANCER_GERMLINE_SNV] is None
    assert args[ObservationsFileWildcards.CANCER_GERMLINE_SV] is None
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


def test_get_variant_callers(analysis_api_balsamic: MockBalsamicAnalysis, case_id: str):
    """Test variant callers extraction for TN-PANEL analysis."""

    # GIVEN a mock metadata object
    balsamic_metadata: BalsamicAnalysis = analysis_api_balsamic.get_latest_metadata(case_id)

    # GIVEN an expected output for tumor normal panel analysis
    expected_callers = [
        "manta (v1.6.0)",
        "cnvkit",
        "vardict (v2019.06.04=pl526_0)",
        "dnascope",
        "tnhaplotyper",
        "manta_germline (v1.6.0)",
        "haplotypecaller",
        "TNscope_umi",
        "delly (v0.8.7)",
    ]

    # WHEN retrieving the analysis variant callers
    variant_callers: list[str] = analysis_api_balsamic.get_variant_callers(balsamic_metadata)

    # THEN check that the callers are correctly identified
    assert variant_callers == expected_callers


def test_get_variant_caller_version(analysis_api_balsamic: MockBalsamicAnalysis, case_id: str):
    """Tests variant caller version extraction."""

    # GIVEN a tool name and a mock variant caller versions dictionary
    var_caller_name = "manta"
    var_caller_versions: dict[str, list[str]] = analysis_api_balsamic.get_latest_metadata(
        case_id
    ).config.bioinfo_tools_version

    # GIVEN the tools mock version
    expected_version = "1.6.0"

    # WHEN retrieving the version of a specific variant caller
    version: str | None = analysis_api_balsamic.get_variant_caller_version(
        var_caller_name, var_caller_versions
    )

    # THEN verify that the extracted version is correct
    assert version == expected_version
