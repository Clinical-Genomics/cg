import pytest
from cg.utils import Process

@pytest.fixture(scope='function')
def ls_process():
    """
        list files process
    """
    binary = 'ls'
    process = Process(binary=binary)
    return process
