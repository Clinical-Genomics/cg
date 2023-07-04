"""Tests for cleaning demultiplexed-runs using
cg.meta.clean.demultiplexed_flow_cells.DemultiplexedRunsFlowCell"""
from pathlib import Path
from typing import Optional
from unittest import mock

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.tb import TrailblazerAPI
from cg.meta.clean.demultiplexed_flow_cells import DemultiplexedRunsFlowCell
from cg.store import Store
from cg.store.models import Flowcell


@pytest.mark.parametrize(
    "bcl2fastq_flow_cell_dir, result",
    [
        ("correct_flow_cell_path", True),
        ("incorrect_flow_cell_path_too_long", False),
        ("incorrect_flow_cell_path_extension", False),
    ],
)
@mock.patch("cg.apps.tb.api.TrailblazerAPI")
@mock.patch("cg.apps.housekeeper.hk.HousekeeperAPI")
@mock.patch("cg.store.Store")
def test_flow_cell_name(
    mock_statusdb: Store,
    mock_hk: HousekeeperAPI,
    mock_tb: TrailblazerAPI,
    bcl2fastq_flow_cell_dir: Path,
    result: bool,
    request,
):
    # GIVEN a flow cell
    flow_cell_path = request.getfixturevalue(bcl2fastq_flow_cell_dir)
    mock_hk.files.return_value.count.return_value = 1
    flow_cell_obj = DemultiplexedRunsFlowCell(
        flow_cell_path=flow_cell_path,
        status_db=mock_statusdb,
        housekeeper_api=mock_hk,
        trailblazer_api=mock_tb,
    )

    # WHEN checking the name of the flow cell

    # THEN the attribute is_correctly_named should be set correctly
    assert flow_cell_obj.is_correctly_named == result


@pytest.mark.parametrize(
    "bcl2fastq_flow_cell_dir, statusdb_return_value, result",
    [
        ("correct_flow_cell_path", Flowcell(), True),
        ("non-existent_flow_cell_path", None, False),
    ],
)
@mock.patch("cg.apps.tb.api.TrailblazerAPI")
@mock.patch("cg.apps.housekeeper.hk.HousekeeperAPI")
@mock.patch("cg.store.Store")
def test_flow_cell_exists_in_statusdb_(
    mock_statusdb: Store,
    mock_hk: HousekeeperAPI,
    mock_tb: TrailblazerAPI,
    bcl2fastq_flow_cell_dir: Path,
    statusdb_return_value: Optional[Flowcell],
    result: bool,
    request,
):
    # GIVEN a flow cell that exists in statusdb
    flow_cell_path = request.getfixturevalue(bcl2fastq_flow_cell_dir)
    mock_statusdb.get_flow_cell_by_name.return_value = statusdb_return_value
    mock_hk.files.return_value.count.return_value = 1
    flow_cell_obj = DemultiplexedRunsFlowCell(
        flow_cell_path=flow_cell_path,
        status_db=mock_statusdb,
        housekeeper_api=mock_hk,
        trailblazer_api=mock_tb,
    )

    # WHEN checking if the flow cell exists in statusdb

    # THEN the attribute is_correctly_named should be set correctly
    assert flow_cell_obj.exists_in_statusdb == result


@mock.patch("cg.apps.tb.api.TrailblazerAPI")
@mock.patch("cg.apps.housekeeper.hk.HousekeeperAPI")
@mock.patch("cg.store.Store")
def test_check_fastq_files_exist_in_hk(
    mock_statusdb: Store, mock_hk: HousekeeperAPI, mock_tb: TrailblazerAPI, correct_flow_cell_path
):
    # GIVEN a flow cell that has fastq files in housekeeper
    flow_cell_obj = DemultiplexedRunsFlowCell(
        flow_cell_path=correct_flow_cell_path,
        status_db=mock_statusdb,
        housekeeper_api=mock_hk,
        trailblazer_api=mock_tb,
    )
    flow_cell_obj._hk_fastq_files = ["file.fastq.gz"]

    # WHEN checking for fastq files in Housekeeper

    # THEN the check should return True
    assert flow_cell_obj.fastq_files_exist_in_housekeeper


@mock.patch("cg.apps.tb.api.TrailblazerAPI")
@mock.patch("cg.apps.housekeeper.hk.HousekeeperAPI")
@mock.patch("cg.store.Store")
def test_check_no_fastq_files_exist_in_hk(
    mock_statusdb: Store, mock_hk: HousekeeperAPI, mock_tb: TrailblazerAPI, correct_flow_cell_path
):
    # GIVEN a flow cell that has no fastq files in housekeeper
    flow_cell_obj = DemultiplexedRunsFlowCell(
        flow_cell_path=correct_flow_cell_path,
        status_db=mock_statusdb,
        housekeeper_api=mock_hk,
        trailblazer_api=mock_tb,
    )
    flow_cell_obj._hk_fastq_files = []

    # WHEN checking for fastq files in Housekeeper

    # THEN the check set the property to False
    assert not flow_cell_obj.fastq_files_exist_in_housekeeper
