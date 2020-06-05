"""Fixtures for cli compress functions"""

from typing import List

import pytest


class MockCompressAPI:
    """Mock out necessary functions for running the compress CLI functions"""

    def __init__(self):
        """initialize mock"""
        self.ntasks = 12
        self.mem = 50
        self.fastq_compression_success = True

    def compress_fastq(self, sample_id: str, dry_run: bool = False):
        """Return if compression was succesfull"""
        return self.fastq_compression_success


class MockLink:
    """Mock a link object"""

    def __init__(self, sample_id):
        """initialize mock"""
        self.sample = MockCase(sample_id)

    def __repr__(self):
        return f"Link:sample={self.sample}"


class MockCase:
    def __init__(self, case_id: str, samples: List[str] = None):
        samples = samples or []
        self.internal_id = case_id
        self.links = [MockLink(sample_id) for sample_id in samples]

    def __repr__(self):
        return f"Case:internal_id={self.internal_id}, links={self.links}"


class MockCompressStore:
    """Mock out necessary functions for using store in compress cli functions"""

    def __init__(self, cases: dict = None):
        """initialize mock"""

        self._families = []
        if cases:
            for case_id in cases:
                self._families.append(MockCase(case_id, samples=cases[case_id]))

    def families(self):
        """Fetch families"""
        return self._families

    def family(self, case_id):
        """Fetch family"""
        if self._families:
            return self._families[0]
        return None

    def __repr__(self):
        return f"Store:samples={self._families}"


@pytest.fixture(name="compress_api")
def fixture_compress_api():
    """Return a compress context"""
    return MockCompressAPI()


@pytest.fixture(name="compress_store")
def fixture_compress_store():
    """Return a compress context"""
    return MockCompressStore()


@pytest.fixture(name="populated_compress_store")
def fixture_populated_compress_store(case_id, samples):
    """Return a populated compress store"""
    cases = {case_id: samples}
    return MockCompressStore(cases)


@pytest.fixture(name="samples")
def fixture_samples():
    """Return a list of sample ids"""
    return ["sample1", "sample2", "sample3"]


@pytest.fixture(name="compress_context")
def fixture_base_compress_context(compress_api, compress_store):
    """Return a compress context"""
    ctx = {"compress": compress_api, "db": compress_store}
    return ctx


@pytest.fixture(name="populated_compress_context")
def fixture_populated_compress_context(compress_api, populated_compress_store):
    """Return a compress context"""
    ctx = {"compress": compress_api, "db": populated_compress_store}
    return ctx
