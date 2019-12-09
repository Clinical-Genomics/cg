"""
Tests for command module
"""
from subprocess import CalledProcessError

import pytest
from cg.utils import Process


def test_process():
    # GIVEN a binary with 'ls'
    binary = "ls"
    # WHEN instantiating a Process with the binary
    process = Process(binary=binary)
    # THEN assert the instatiation worked as expected
    assert process.binary == binary
    assert repr(process) == "Process:base_call:['ls']"
    assert process.stdout == ""


def test_process_run_invalid_command():
    # GIVEN a binary with 'ls'
    binary = "false"
    # WHEN instantiating a Process with the binary
    process = Process(binary=binary)
    # THEN assert the instatiation worked as expected
    with pytest.raises(CalledProcessError):
        process.run_command()


def test_process_run_command_no_params(ls_process):
    # GIVEN a proces with 'ls' as binary
    process = ls_process
    # WHEN running the command without parameters
    res = process.run_command()
    # THEN assert it returns valid exit code
    assert res == 0
    # THEN assert the output is valid
    assert "setup.py" in process.stdout


def test_process_run_command_with_params(ls_process):
    # GIVEN a proces with 'ls' as binary
    process = ls_process
    # WHEN running the command with parameters
    res = process.run_command(["-l"])
    # THEN assert it returns valid exit code
    assert res == 0
    # THEN assert the output is valid
    i = 0
    for i, line in enumerate(process.stdout.split("\n"), 1):
        if i > 1:
            assert len(line.split()) == 9
    assert i > 1


def test_iter_output_lines(ls_process):
    # GIVEN a proces with 'ls' as binary
    process = ls_process
    # WHEN running the command without parameters
    process.run_command()
    # THEN assert it returns valid exit code
    # THEN assert the output is valid
    i = 0
    for i, line in enumerate(process.stdout_lines(), 1):
        pass
    assert i > 0


def test_iter_stderr_lines(ls_process, stderr_output):
    # GIVEN a proces with some stderr output
    process = ls_process
    process.stderr = stderr_output
    # WHEN running the command without parameters
    # THEN assert there where lines to iterate
    i = 0
    for i, line in enumerate(process.stderr_lines(), 1):
        pass
    assert i > 0


def test_iter_stderr_lines_no_output(ls_process):
    # GIVEN a proces with some stderr output
    process = ls_process
    # WHEN running the command without parameters
    # THEN assert there where lines to iterate
    i = 0
    for i, line in enumerate(process.stderr_lines(), 1):
        assert line == ""
    assert i == 1
