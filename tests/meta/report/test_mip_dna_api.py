from cg.constants import REPORT_GENDER


def test_get_sample_metadata(
    report_api_mip_dna, mip_analysis_api, case_mip_dna, sample_store, helpers
):
    """Tests sample metadata extraction."""

    # GIVEN a mock sample and the latest metadata
    sample = helpers.add_sample(sample_store)
    sample.internal_id = "ADM1"
    sample.reads = None
    mip_metadata = mip_analysis_api.get_latest_metadata(case_mip_dna.internal_id)

    # GIVEN the expected output
    expected_metadata = {
        "million_read_pairs": "N/A",
        "duplicates": "4.01",
        "bait_set": "N/A",
        "gender": REPORT_GENDER.get("male"),
        "mapped_reads": "99.77",
        "mean_target_coverage": "38.34",
        "pct_10x": "99.1",
    }

    # WHEN retrieving the sample metadata
    sample_metadata = report_api_mip_dna.get_sample_metadata(case_mip_dna, sample, mip_metadata)

    # THEN check that the sample metadata is correctly retrieved
    assert sample_metadata == expected_metadata


def test_get_sample_coverage(report_api_mip_dna, sample_store, helpers, case_mip_dna):
    """Checks the sample coverage retrieval from Chanjo."""

    # GIVEN a case and a sample with a specific ID
    case_mip_dna.panels = []
    sample = helpers.add_sample(sample_store)
    sample.internal_id = "ADM2"

    # WHEN retrieving the sample coverage
    sample_coverage = report_api_mip_dna.get_sample_coverage(sample, case_mip_dna)

    # THEN assert that the extracted values are the expected ones
    assert sample_coverage == {"mean_coverage": 37.342, "mean_completeness": 97.1}


def test_get_report_accreditation(report_api_mip_dna, mip_analysis_api, case_mip_dna):
    """Verifies the report accreditation extraction workflow."""

    # GIVEN a list of accredited samples
    mip_metadata = mip_analysis_api.get_latest_metadata(case_mip_dna.internal_id)
    samples = report_api_mip_dna.get_samples_data(case_mip_dna, mip_metadata)

    # WHEN retrieving the report accreditation
    accredited = report_api_mip_dna.get_report_accreditation(samples)

    # THEN check that the report is accredited
    assert accredited


def test_get_report_accreditation_false(report_api_mip_dna, mip_analysis_api, case_mip_dna):
    """Verifies that the report is not accredited if it contains a sample application that is not accredited."""

    # GIVEN a list of samples when one of them is not accredited
    mip_metadata = mip_analysis_api.get_latest_metadata(case_mip_dna.internal_id)
    samples = report_api_mip_dna.get_samples_data(case_mip_dna, mip_metadata)
    samples[0].application.accredited = False

    # WHEN retrieving the report accreditation
    accredited = report_api_mip_dna.get_report_accreditation(samples)

    # THEN check that the report is not accredited
    assert not accredited
