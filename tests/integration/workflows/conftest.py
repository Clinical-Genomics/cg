from pathlib import Path

import pytest
from pytest import TempPathFactory

from cg.constants.constants import Workflow


@pytest.fixture(autouse=True)
def current_workflow() -> Workflow:
    raise NotImplementedError("Please add a current_workflow fixture to your integration test")


@pytest.fixture()
def root_dir(current_workflow: Workflow, tmp_path_factory: TempPathFactory):
    test_root_dir: Path = tmp_path_factory.mktemp(current_workflow)
    return test_root_dir
