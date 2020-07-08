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


# Store fixtures


class CaseInfo:
    """Holds information for creating a case"""

    def __init__(self, **kwargs):
        self.case_id = kwargs["case_id"]
        self.family_name = kwargs["family_name"]
        self.timestamp = kwargs["timestamp"]
        self.later_timestamp = kwargs["later_timestamp"]
        self.application_tag = kwargs["application_tag"]


@pytest.fixture(name="compress_case_info")
def fixture_compress_case_info(
    case_id, family_name, timestamp, later_timestamp, wgs_application_tag,
):
    """Returns a object with information about a case"""
    return CaseInfo(
        case_id=case_id,
        family_name=family_name,
        timestamp=timestamp,
        later_timestamp=later_timestamp,
        application_tag=wgs_application_tag,
    )


@pytest.fixture(name="populated_compress_store")
def fixture_populated_compress_store(store, helpers, compress_case_info, analysis_family):
    """Return a store populated with a completed analysis"""
    # Make sure that there is a family where anaylsis is completer
    helpers.ensure_family(
        store,
        family_info=analysis_family,
        app_tag=compress_case_info.application_tag,
        ordered_at=compress_case_info.timestamp,
        completed_at=compress_case_info.later_timestamp,
    )

    return store


@pytest.fixture(name="populated_compress_multiple_store")
def fixture_populated_compress_multiple_store(
    store, helpers, compress_case_info, analysis_family,
):
    """Return a store populated with multiple completed analysis"""
    case_id = compress_case_info.case_id
    family_name = compress_case_info.family_name
    for number in range(10):
        analysis_family["internal_id"] = "_".join([str(number), case_id])
        analysis_family["name"] = "_".join([str(number), family_name])

        helpers.ensure_family(
            store,
            family_info=analysis_family,
            app_tag=compress_case_info.application_tag,
            ordered_at=compress_case_info.timestamp,
            completed_at=compress_case_info.later_timestamp,
        )

    return store


# Context fixtures


@pytest.fixture(name="compress_context")
def fixture_base_compress_context(compress_api, store):
    """Return a compress context"""
    ctx = {"compress": compress_api, "db": store}
    return ctx


@pytest.fixture(name="populated_multiple_compress_context")
def fixture_populated_multiple_compress_context(compress_api, populated_compress_multiple_store):
    """Return a compress context populated with a completed analysis"""
    # Make sure that there is a family where anaylis is completer
    return {"compress": compress_api, "db": populated_compress_multiple_store}


@pytest.fixture(name="populated_compress_context")
def fixture_populated_compress_context(compress_api, populated_compress_store):
    """Return a compress context populated with a completed analysis"""
    # Make sure that there is a family where anaylis is completer
    return {"compress": compress_api, "db": populated_compress_store}
