import copy
from typing import Dict

from cg.models.report.metadata import BalsamicTargetedSampleMetadataModel

from cg.store import Store

from cg.meta.report.balsamic import BalsamicReportAPI

from cg.models.balsamic.analysis import BalsamicAnalysis

from cg.store.models import BedVersion, Sample, Family
from tests.store_helpers import StoreHelpers


def test_get_sample_metadata(
    report_api_balsamic: BalsamicReportAPI,
    case_balsamic: Family,
    helpers: StoreHelpers,
    sample_store: Store,
):
    """Test sample metadata extraction."""

    # GIVEN a tumor sample, a bed version, and the latest metadata
    sample: Sample = helpers.add_sample(store=sample_store)
    sample.internal_id = "ACC0000A1"
    sample.reads = 20000000
    bed_name: str = "GIcfDNA"
    bed_version: BedVersion = helpers.ensure_bed_version(store=sample_store, bed_name=bed_name)
    bed_version.filename = "gicfdna_3.1_hg19_design.bed"
    balsamic_metadata: BalsamicAnalysis = report_api_balsamic.analysis_api.get_latest_metadata(
        case_balsamic.internal_id
    )

    # GIVEN the expected output
    expected_metadata: Dict[str, str] = {
        "million_read_pairs": "10.0",
        "duplicates": "93.1",
        "mean_insert_size": "178.19",
        "fold_80": "1.16",
        "bait_set": bed_name,
        "bait_set_version": "3.1",
        "median_target_coverage": "5323.0",
        "pct_250x": "N/A",
        "pct_500x": "N/A",
    }

    # WHEN retrieving the sample metadata
    sample_metadata: BalsamicTargetedSampleMetadataModel = report_api_balsamic.get_sample_metadata(
        case=case_balsamic, sample=sample, analysis_metadata=balsamic_metadata
    )

    # THEN check that the sample metadata is correctly retrieved
    assert sample_metadata.dict() == expected_metadata


def test_get_variant_callers(report_api_balsamic, case_id):
    """Test variant callers extraction for TN-PANEL analysis."""

    # GIVEN a mock metadata object
    balsamic_metadata = report_api_balsamic.analysis_api.get_latest_metadata(case_id)

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
    variant_callers = report_api_balsamic.get_variant_callers(balsamic_metadata)

    # THEN check that the callers are correctly identified
    assert variant_callers == expected_callers


def test_get_variant_caller_version(report_api_balsamic, case_id):
    """Tests variant caller version extraction."""

    # GIVEN a tool name and a mock variant caller versions dictionary
    var_caller_name = "manta"
    var_caller_versions = report_api_balsamic.analysis_api.get_latest_metadata(
        case_id
    ).config.bioinfo_tools_version

    # GIVEN the tools mock version
    expected_version = "1.6.0"

    # WHEN retrieving the version of a specific variant caller
    version = report_api_balsamic.get_variant_caller_version(var_caller_name, var_caller_versions)

    # THEN verify that the extracted version is correct
    assert version == expected_version


def test_get_report_accreditation(report_api_balsamic, case_id):
    """Tests report accreditation for a specific BALSAMIC analysis."""

    # GIVEN a mock metadata object and an accredited one
    balsamic_metadata = report_api_balsamic.analysis_api.get_latest_metadata(case_id)

    balsamic_accredited_metadata = copy.deepcopy(balsamic_metadata)
    balsamic_accredited_metadata.config.panel.capture_kit = "gmsmyeloid"

    # WHEN performing the accreditation validation
    unaccredited_report = report_api_balsamic.get_report_accreditation(None, balsamic_metadata)
    accredited_report = report_api_balsamic.get_report_accreditation(
        None, balsamic_accredited_metadata
    )

    # THEN verify that only the panel "gmsmyeloid" reports are validated
    assert not unaccredited_report
    assert accredited_report
