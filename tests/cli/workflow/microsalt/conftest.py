""" Fixtures for microsalt CLI test """

from pathlib import Path

import pytest

from cg.apps.hermes.hermes_api import HermesApi
from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.store import Store


@pytest.fixture(scope="function")
def base_context(
    context_config,
):
    """ The click context for the microsalt cli """
    return {
        "analysis_api": MicrosaltAnalysisAPI(context_config),
    }


@pytest.fixture(name="microbial_sample_id")
def fixture_microbial_sample_id():
    """ Define a name for a microbial sample """
    return "microbial_sample_id"


@pytest.fixture(name="microbial_sample_name")
def fixture_microbial_sample_name():
    """ Define a name for a microbial sample """
    return "microbial_sample_name"


@pytest.fixture(name="microbial_ticket")
def fixture_microbial_ticket():
    """ Define a ticket for a microbial order """
    return "123456"


@pytest.fixture(scope="function")
def invalid_ticket_number() -> str:
    return "1234560000"
