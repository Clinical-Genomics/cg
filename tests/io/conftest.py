import pytest


@pytest.fixture(name="yaml_stream")
def yaml_stream() -> str:
    """Return string with yaml format"""
    _content = """
- "Lorem"
- 'ipsum'
- 'sit'
- "amet"
"""
    return _content
