"""Fixtures for cli compress functions"""

import pytest


class MockCompressAPI:
    """Mock out necessary functions for running the compress CLI functions"""

    def __init__(self):
        """initialize mock"""
        self.ntasks = 12
        self.mem = 50
        self.fastq_compression_success = True
        self.spring_decompression_success = True
        self.dry_run = False

    def set_dry_run(self, dry_run: bool):
        """Update dry run"""
        self.dry_run = dry_run

    def compress_fastq(self, sample_id: str, dry_run: bool = False):
        """Return if compression was succesfull"""
        _ = sample_id, dry_run
        return self.fastq_compression_success

    def decompress_spring(self, sample_id: str, dry_run: bool = False):
        """Return if decompression was succesfull"""
        _ = sample_id, dry_run
        return self.spring_decompression_success


@pytest.fixture(name="compress_api")
def fixture_compress_api():
    """Return a compress context"""
    return MockCompressAPI()


@pytest.fixture(name="samples")
def fixture_samples():
    """Return a list of sample ids"""
    return ["sample1", "sample2", "sample3"]


@pytest.fixture(name="compress_context")
def fixture_base_compress_context(compress_api, store):
    """Return a compress context"""
    ctx = {"compress": compress_api, "db": store}
    return ctx


@pytest.fixture(name="populated_compress_context")
def fixture_populated_compress_context(
    compress_context, helpers, timestamp, later_timestamp, wgs_application_tag, analysis_family
):
    """Return a compress context populated with a completed analysis"""
    # Make sure that there is a family where anaylis is completer
    helpers.ensure_family(
        compress_context["db"],
        family_info=analysis_family,
        app_tag=wgs_application_tag,
        ordered_at=timestamp,
        completed_at=later_timestamp,
    )

    return compress_context


@pytest.fixture(name="populated_multiple_compress_context")
def fixture_populated_multiple_compress_context(
    compress_context,
    case_id,
    family_name,
    helpers,
    timestamp,
    later_timestamp,
    wgs_application_tag,
    analysis_family,
):
    """Return a compress context populated with a completed analysis"""
    # Make sure that there is a family where anaylis is completer
    for number in range(10):
        analysis_family["internal_id"] = "_".join([str(number), case_id])
        analysis_family["name"] = "_".join([str(number), family_name])

        helpers.ensure_family(
            compress_context["db"],
            family_info=analysis_family,
            app_tag=wgs_application_tag,
            ordered_at=timestamp,
            completed_at=later_timestamp,
        )

    return compress_context
