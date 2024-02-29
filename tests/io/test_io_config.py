from pathlib import Path

import pytest

from cg.io.config import write_config_nextflow_style


def test_write_config_nextflow_style(config_stream: Path):
    """
    Test output content from stream into nextflow config format.
    """
    # GIVEN content

    # WHEN reading the file
    content: dict[str] = write_config_nextflow_style(content=config_stream)

    # THEN assert a config format is returned
    assert content == 'Lorem = "ipsum"\n'
