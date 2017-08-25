import json

import pytest


@pytest.fixture
def scout_order():
    """Load an example scout order."""
    json_path = 'tests/fixtures/orders/scout.json'
    json_data = json.load(open(json_path))
    return json_data


@pytest.fixture
def external_order():
    """Load an example external order."""
    json_path = 'tests/fixtures/orders/external.json'
    json_data = json.load(open(json_path))
    return json_data


@pytest.fixture
def fastq_order():
    """Load an example fastq order."""
    json_path = 'tests/fixtures/orders/fastq.json'
    json_data = json.load(open(json_path))
    return json_data


@pytest.fixture
def rml_order():
    """Load an example rml order."""
    json_path = 'tests/fixtures/orders/rml.json'
    json_data = json.load(open(json_path))
    return json_data
