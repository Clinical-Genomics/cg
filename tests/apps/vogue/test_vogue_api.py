"""
    Tests for VogueAPI
"""
import logging
import subprocess
from unittest import mock

from cg.apps.vogue import VogueAPI


def test_instatiate(vogue_config):

    """Test to instantiate a vogue api"""

    # GIVEN a vogue api with a config

    # WHEN instantiating a vogue api
    vogue_api = VogueAPI(vogue_config)

    # THEN assert that the adapter was properly instantiated
    assert vogue_api.vogue_binary == vogue_config["vogue"]["binary_path"]


def test_load_bioinfo_sample(vogue_config, caplog):

    """Test load bioinfo sample upload in vogue api"""

    # GIVEN a vogue api and a vogue config
    vogue_api = VogueAPI(vogue_config)
    dummy_stdout = "dummy_stdout"
    dummy_stderr = "dummy_stderr"
    dummy_returncode_success = 0
    test_load_bioinfo_sample_inputs = {"analysis_case_name": "dummy_case"}
    load_bioinfo_sample_call = [
        "load",
        "bioinfo",
        "sample",
        "--analysis-case",
        test_load_bioinfo_sample_inputs["analysis_case_name"],
    ]
    load_bioinfo_sample_call_command = " ".join(load_bioinfo_sample_call)
    caplog.set_level(logging.INFO)

    # WHEN instantiating a vogue api and input data
    with mock.patch.object(subprocess, "run") as mocked:
        mocked.return_value.stdout = dummy_stdout.encode("utf-8")
        mocked.return_value.stderr = dummy_stderr.encode("utf-8")
        mocked.return_value.returncode = dummy_returncode_success
        vogue_api.load_bioinfo_sample(load_bioinfo_inputs=test_load_bioinfo_sample_inputs)

        # THEN assert that command is in log output
        assert load_bioinfo_sample_call_command in caplog.text


def test_load_bioinfo_raw(vogue_config, caplog):

    """Test load bioinfo raw upload in vogue api"""

    # GIVEN a vogue api and a vogue config
    vogue_api = VogueAPI(vogue_config)
    dummy_stdout = "dummy_stdout"
    dummy_stderr = "dummy_stderr"
    dummy_returncode_success = 0
    test_load_bioinfo_raw_inputs = {
        "samples": "dummy_sample",
        "analysis_result_file": "dummy_file_name",
        "analysis_type": "dummy_analysis_type",
        "analysis_case_name": "dummy_analysis_case_name",
        "analysis_workflow_version": "dummy_version_3.1415",
        "case_analysis_type": "dummy_multiqc",
        "analysis_workflow_name": "dummy_best_workflow",
    }

    load_bioinfo_raw_call = [
        "load",
        "bioinfo",
        "raw",
        "--sample-list",
        test_load_bioinfo_raw_inputs["samples"],
        "--analysis-result",
        test_load_bioinfo_raw_inputs["analysis_result_file"],
        "--analysis-type",
        test_load_bioinfo_raw_inputs["analysis_type"],
        "--analysis-case",
        test_load_bioinfo_raw_inputs["analysis_case_name"],
        "--workflow-version",
        test_load_bioinfo_raw_inputs["analysis_workflow_version"],
        "--case-analysis-type",
        test_load_bioinfo_raw_inputs["case_analysis_type"],
        "--analysis-workflow",
        test_load_bioinfo_raw_inputs["analysis_workflow_name"],
    ]
    load_bioinfo_raw_call_command = " ".join(load_bioinfo_raw_call)
    caplog.set_level(logging.INFO)

    # WHEN instantiating a vogue api and input data
    with mock.patch.object(subprocess, "run") as mocked:
        mocked.return_value.stdout = dummy_stdout.encode("utf-8")
        mocked.return_value.stderr = dummy_stderr.encode("utf-8")
        mocked.return_value.returncode = dummy_returncode_success
        vogue_api.load_bioinfo_raw(load_bioinfo_inputs=test_load_bioinfo_raw_inputs)

        # THEN assert that command is in log output
        assert load_bioinfo_raw_call_command in caplog.text


def test_load_bioinfo_process(vogue_config, caplog):

    """Test load bioinfo process upload in vogue api"""

    # GIVEN a vogue api and a vogue config
    vogue_api = VogueAPI(vogue_config)
    dummy_stdout = "dummy_stdout"
    dummy_stderr = "dummy_stderr"
    dummy_returncode_success = 0
    test_load_bioinfo_process_inputs = {
        "analysis_type": "dummy_analysis_type",
        "analysis_case_name": "dummy_analysis_case_name",
        "analysis_workflow_name": "dummy_best_workflow",
        "analysis_workflow_version": "dummy_version_3.1415",
        "case_analysis_type": "dummy_multiqc",
    }

    load_bioinfo_process_call = [
        "load",
        "bioinfo",
        "process",
        "--analysis-type",
        test_load_bioinfo_process_inputs["analysis_type"],
        "--analysis-case",
        test_load_bioinfo_process_inputs["analysis_case_name"],
        "--analysis-workflow",
        test_load_bioinfo_process_inputs["analysis_workflow_name"],
        "--workflow-version",
        test_load_bioinfo_process_inputs["analysis_workflow_version"],
        "--case-analysis-type",
        test_load_bioinfo_process_inputs["case_analysis_type"],
    ]

    load_bioinfo_process_call_command = " ".join(load_bioinfo_process_call)
    caplog.set_level(logging.INFO)

    # WHEN instantiating a vogue api and input data
    with mock.patch.object(subprocess, "run") as mocked:
        mocked.return_value.stdout = dummy_stdout.encode("utf-8")
        mocked.return_value.stderr = dummy_stderr.encode("utf-8")
        mocked.return_value.returncode = dummy_returncode_success
        vogue_api.load_bioinfo_process(
            load_bioinfo_inputs=test_load_bioinfo_process_inputs,
            cleanup_flag=True,
        )

        # THEN assert that command is in log output
        assert load_bioinfo_process_call_command in caplog.text


def test_vogue_load_reagent_labels(vogue_api, caplog):
    caplog.set_level(logging.DEBUG)
    # GIVEN a vogue api

    # WHEN running vogue load reagent_label with some days as argument
    vogue_api.load_reagent_labels(days=1)

    # THEN assert vogue output is comunicated
    assert "vogue output" in caplog.text


def test_vogue_load_samples(vogue_api, caplog):
    caplog.set_level(logging.DEBUG)

    # GIVEN a vogue api

    # WHEN running vogue load samples with some days as argument
    vogue_api.load_samples(days=1)

    # THEN assert vogue output is comunicated
    assert "vogue output" in caplog.text


def test_vogue_load_flowcells(vogue_api, caplog):
    caplog.set_level(logging.DEBUG)
    # GIVEN a vogue api

    # WHEN running vogue load flowcells with some days as argument
    vogue_api.load_flowcells(days=1)

    # THEN assert vogue output is comunicated
    assert "vogue output" in caplog.text
