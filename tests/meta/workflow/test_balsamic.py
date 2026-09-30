"""Tests for BALSAMIC analysis."""

from cg.models.balsamic.analysis import BalsamicAnalysis
from tests.mocks.balsamic_analysis_mock import MockBalsamicAnalysis


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
    ).balsamic_config.bioinfo_tools_version

    # GIVEN the tools mock version
    expected_version = "1.6.0"

    # WHEN retrieving the version of a specific variant caller
    version: str | None = analysis_api_balsamic.get_variant_caller_version(
        var_caller_name, var_caller_versions
    )

    # THEN verify that the extracted version is correct
    assert version == expected_version
