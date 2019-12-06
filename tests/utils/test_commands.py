from cg.utils import Process

def test_process():
    # GIVEN a binary with 'ls'
    binary = 'ls'
    # WHEN instantiating a Process with the binary
    process = Process(binary=binary)
    # THEN assert the instatiation worked as expected
    assert process.binary == binary
    assert repr(process) == "Process:base_call:['ls']"
    assert process.stdout == ""

def test_process_run_command_no_params(ls_process):
    # GIVEN a proces with 'ls' as binary
    process = ls_process
    # WHEN running the command without parameters
    res = process.run_command()
    # THEN assert it returns valid exit code
    assert res == 0
    # THEN assert the output is valid
    assert 'setup.py' in process.stdout
    

def test_process_run_command_with_params(ls_process):
    # GIVEN a proces with 'ls' as binary
    process = ls_process
    # WHEN running the command without parameters
    res = process.run_command()
    # THEN assert it returns valid exit code
    assert res == 0
    # THEN assert the output is valid
    assert 'setup.py' in process.stdout
    