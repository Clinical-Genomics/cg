from pathlib import Path

import pytest

from cg.io.config import write_config_nextflow_style


def test_write_config_nextflow_style(config_dict: Path):
    """
    Test output content from stream into nextflow config format.
    """

    # THEN assert a config format is returned
    assert (
        write_config_nextflow_style(content=config_dict)
        == 'params.input = "input_path"\nparams.output = "output_path"\n'
    )
