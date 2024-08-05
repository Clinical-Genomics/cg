import copy

from cg.constants.report import NA_FIELD, REPORT_QC_FLAG
from cg.meta.report.balsamic import BalsamicReportAPI
from cg.models.balsamic.analysis import BalsamicAnalysis
from cg.models.report.metadata import BalsamicTargetedSampleMetadataModel
from cg.store.models import BedVersion, Case, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_get_sample_metadata(
    report_api_balsamic: BalsamicReportAPI,
    case_balsamic: Case,
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
    expected_metadata: dict[str, str] = {
        "bait_set": bed_name,
        "bait_set_version": "3.1",
        "duplicates": "93.1",
        "fold_80": "1.16",
        "gc_dropout": "1.01",
        "initial_qc": REPORT_QC_FLAG.get(True),
        "mean_insert_size": "178.19",
        "median_target_coverage": "5323.0",
        "million_read_pairs": "10.0",
        "pct_250x": NA_FIELD,
        "pct_500x": NA_FIELD,
    }

    # WHEN retrieving the sample metadata
    sample_metadata: BalsamicTargetedSampleMetadataModel = report_api_balsamic.get_sample_metadata(
        case=case_balsamic, sample=sample, analysis_metadata=balsamic_metadata
    )

    # THEN check that the sample metadata is correctly retrieved
    assert sample_metadata.model_dump() == expected_metadata


def test_is_report_accredited(report_api_balsamic, case_id):
    """Test report accreditation for a specific BALSAMIC analysis."""

    # GIVEN a mock metadata object and an accredited one
    balsamic_metadata = report_api_balsamic.analysis_api.get_latest_metadata(case_id)

    balsamic_accredited_metadata = copy.deepcopy(balsamic_metadata)
    balsamic_accredited_metadata.config.panel.capture_kit = "gmsmyeloid"

    # WHEN performing the accreditation validation
    unaccredited_report = report_api_balsamic.is_report_accredited(None, balsamic_metadata)
    accredited_report = report_api_balsamic.is_report_accredited(None, balsamic_accredited_metadata)

    # THEN verify that only the panel "gmsmyeloid" reports are validated
    assert not unaccredited_report
    assert accredited_report
