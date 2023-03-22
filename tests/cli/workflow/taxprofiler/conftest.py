"""Fixtures for cli workflow taxprofiler tests"""

import datetime as dt
import gzip
from pathlib import Path
from typing import List

import pytest

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Pipeline
from cg.constants.constants import FileFormat
from cg.io.controller import WriteFile, WriteStream
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Family, Sample
from tests.mocks.limsmock import MockLimsAPI
from tests.mocks.process_mock import ProcessMock
from tests.mocks.tb_mock import MockTB
from tests.store_helpers import StoreHelpers


@pytest.fixture(scope="function", name="taxprofiler_context")
def fixture_taxprofiler_context(
    cg_context: CGConfig,
) -> CGConfig:
    """context to use in cli"""
    cg_context.meta_apis["analysis_api"] = TaxprofilerAnalysisAPI(config=cg_context)
    return cg_context
