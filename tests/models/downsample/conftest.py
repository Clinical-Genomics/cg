"""Fixtures for testing the downsample module."""
from pathlib import Path
from typing import Dict

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.store import Store
from cg.store.models import Family, Sample
from tests.store_helpers import StoreHelpers
