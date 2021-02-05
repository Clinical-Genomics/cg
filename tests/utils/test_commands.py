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
    # THEN assert the instantiation worked as expected
    assert process.binary == binary
    assert repr(process) == "Process:base_call:['ls']"
    assert process.stdout == ""


def test_process_run_invalid_command():
    # GIVEN a binary with non existing command
    binary = "false"
    process = Process(binary=binary)
    # WHEN running the command
    with pytest.raises(CalledProcessError):
        # THEN assert an exception is raised
        process.run_command()


def test_process_run_command_no_params(ls_process):
    # GIVEN a proces with 'ls' as binary
    process = ls_process
    # WHEN running the command without parameters
    process.run_command()
    # THEN assert stdout is captures in self.stdout
    assert "README" in process.stdout


def test_process_run_command_with_params(ls_process):
    # GIVEN a process with 'ls' as binary
    process = ls_process
    # WHEN running the command with parameters
    process.run_command(parameters=["-l"])
    # THEN assert the output is valid
    i = 0
    for i, line in enumerate(process.stdout.split("\n"), 1):
        if i > 1:
            assert len(line.split()) >= 9
    assert i > 1


def test_process_std_err(ls_process):
    # GIVEN a proces with 'ls' as binary
    process = ls_process
    # WHEN running the command with invalid parameters
    with pytest.raises(CalledProcessError):
        # THEN assert that a exception is raised
        process.run_command(parameters=["-kffd4"])
    # THEN assert that stderr was captured
    assert process.stderr


def test_iter_output_lines(ls_process):
    # GIVEN a proces with 'ls' as binary
    process = ls_process
    # WHEN running the command without parameters
    process.run_command()
    nr_output_lines = 0
    for nr_output_lines, _line in enumerate(process.stdout_lines(), 1):
        pass
    # THEN assert that the method returns some lines
    assert nr_output_lines > 0


def test_iter_stderr_lines(ls_process, stderr_output):
    # GIVEN a proces with some stderr output
    process = ls_process
    process.stderr = stderr_output
    # WHEN running the command without parameters
    # THEN assert there where lines to iterate
    nr_stderr_lines = 0
    for nr_stderr_lines, _line in enumerate(process.stderr_lines(), 1):
        pass
    assert nr_stderr_lines > 0


def test_iter_stderr_lines_no_output(ls_process):
    # GIVEN a proces with some stderr output
    process = ls_process
    # WHEN running the command without parameters
    # THEN assert there where lines to iterate
    i = 0
    for i, line in enumerate(process.stderr_lines(), 1):
        assert line == ""
    assert i == 1
