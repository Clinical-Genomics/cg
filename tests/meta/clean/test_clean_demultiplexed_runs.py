"""Tests for cleaning demultiplexed-runs using
cg.meta.clean.demultiplexed_flowcells.DemuxedFlowcell """
from pathlib import Path
from typing import Optional
from unittest import mock

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.clean.demultiplexed_flowcells import DemuxedFlowcell
from cg.store import Store
from cg.store.models import Flowcell


@pytest.mark.parametrize(
    "flowcell_path, result",
    [
        ("correct_flowcell_path", True),
        ("incorrect_flowcell_path_too_long", False),
        ("incorrect_flowcell_path_extension", False),
    ],
)
@mock.patch("cg.apps.housekeeper.hk.HousekeeperAPI")
@mock.patch("cg.store.Store")
def test_flowcell_name(
    mock_statusdb: Store, mock_hk: HousekeeperAPI, flowcell_path: Path, result: bool, request
):
    # GIVEN a flowcell
    flowcell_path = request.getfixturevalue(flowcell_path)
    flowcell_obj = DemuxedFlowcell(
        flowcell_path=flowcell_path, status_db=mock_statusdb, housekeeper_api=mock_hk
    )

    # WHEN checking the name of the flowcell
    flowcell_obj.check_flowcell_naming()

    # THEN the attribute is_correctly_named should be set correctly
    assert flowcell_obj.is_correctly_named == result


@pytest.mark.parametrize(
    "flowcell_path, statusdb_return_value, result",
    [
        ("correct_flowcell_path", Flowcell(), True),
        ("nonexistent_flowcell_path", None, False),
    ],
)
@mock.patch("cg.apps.housekeeper.hk.HousekeeperAPI")
@mock.patch("cg.store.Store")
def test_flowcell_exists_in_statusdb_(
    mock_statusdb: Store,
    mock_hk: HousekeeperAPI,
    flowcell_path: Path,
    statusdb_return_value: Optional[Flowcell],
    result: bool,
    request,
):
    # GIVEN a flowcell that exists in statusdb
    flowcell_path = request.getfixturevalue(flowcell_path)
    mock_statusdb.flowcell.return_value = statusdb_return_value
    flowcell_obj = DemuxedFlowcell(
        flowcell_path=flowcell_path, status_db=mock_statusdb, housekeeper_api=mock_hk
    )

    # WHEN checking if the flowcell exists in statusdb
    flowcell_obj.check_flowcell_exists_in_status_db()

    # THEN the attribute is_correctly_named should be set correctly
    assert flowcell_obj.exists_in_status_db == result
