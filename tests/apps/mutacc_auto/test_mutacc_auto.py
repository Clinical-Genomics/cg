""" Tests for cg.apps.mutacc_auto module"""

import subprocess

import pytest
from cg.apps.mutacc_auto import MutaccAutoAPI, run_command


def test_instatiate(mutacc_config):
    """ Test to instatiate an MutaccAutoAPI object """
    # GIVEN a dict with config data to

    # WHEN instatiating a mutacc_auto API

    mutacc_api = MutaccAutoAPI(config=mutacc_config)

    # THEN the object attributes are set correctly

    assert mutacc_api.mutacc_auto_config == mutacc_config["mutacc_auto"]["config_path"]
    assert mutacc_api.mutacc_auto_binary == mutacc_config["mutacc_auto"]["binary_path"]
    assert mutacc_api.mutacc_padding == mutacc_config["mutacc_auto"]["padding"]
    assert mutacc_api.base_call == [
        mutacc_config["mutacc_auto"]["binary_path"],
        "--config-file",
        mutacc_config["mutacc_auto"]["config_path"],
    ]


def test_extract_reads(mutacc_auto_api, mocker):
    """
    Test extract_reads method
    """
    # GIVEN a mutacc-auto api a case, and list of variants
    case = {}
    variants = []
    # WHEN calling MutaccAutoAPI.extract_reads

    # patch the run_command funciton
    mock_run_command = mocker.patch("cg.apps.mutacc_auto.run_command")
    mutacc_auto_api.extract_reads(case, variants)

    # THEN the command and its options should be as expected
    expected_call = mutacc_auto_api.base_call + [
        "extract",
        "--variants",
        str(variants),
        "--case",
        str(case),
        "--padding",
        str(mutacc_auto_api.mutacc_padding),
    ]

    mock_run_command.assert_called_with(expected_call)


def test_import_reads(mutacc_auto_api, mocker):
    """
    Test import_reads method
    """
    # GIVEN a mutacc-auto api

    # WHEN calling MutaccAutoAPI.import_reads

    mock_run_command = mocker.patch("cg.apps.mutacc_auto.run_command")
    mutacc_auto_api.import_reads()

    # THEN command and its options should be as expected
    expected_call = mutacc_auto_api.base_call + ["import"]
    mock_run_command.assert_called_with(expected_call)


def test_run_command(mock_failed_process, mocker):

    """
    Test run_command function
    """
    # WITH a mocked subprocess.run function
    mocker.patch.object(subprocess, "run")
    subprocess.run.return_value = mock_failed_process

    # WHEN trying to run a command with run_command

    # Then Error subprocess.CalledProcessError is raised
    with pytest.raises(subprocess.CalledProcessError):

        run_command(["command"])
