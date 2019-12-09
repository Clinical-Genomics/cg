import pytest
from cg.utils import Process


@pytest.fixture(scope="function")
def ls_process():
    """
        list files process
    """
    binary = "ls"
    process = Process(binary=binary)
    return process


@pytest.fixture(scope="function")
def echo_process():
    """
        list files process
    """
    binary = "echo"
    process = Process(binary=binary)
    return process


@pytest.fixture(scope="function")
def stderr_output():
    """
        list files process
    """
    lines = (
        "2018-11-29 08:41:38 130-229-8-20-dhcp.local "
        "mongo_adapter.client[77135] INFO Connecting to "
        "uri:mongodb://None:None@localhost:27017\n"
        "2018-11-29 08:41:38 130-229-8-20-dhcp.local "
        "mongo_adapter.client[77135] INFO Connection "
        "established\n"
    )
    return lines
