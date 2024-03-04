"""
    conftest for genotype API
"""

import pytest

from cg.constants.constants import FileFormat
from cg.constants.subject import Sex
from cg.io.controller import WriteStream


@pytest.fixture
def genotype_export_sample_output(genotype_config: dict) -> str:
    """
    genotype API fixture
    """
    sample_output = {
        "ACC6987A15": {
            "status": None,
            "sample_created_in_genotype_db": "2020-07-15",
            "sex": Sex.FEMALE,
            "comment": None,
        },
        "ACC6987A16": {
            "status": None,
            "sample_created_in_genotype_db": "2020-07-15",
            "sex": Sex.FEMALE,
            "comment": None,
        },
    }
    return WriteStream.write_stream_from_content(content=sample_output, file_format=FileFormat.JSON)


@pytest.fixture
def genotype_export_sample_analysis_output() -> str:
    """Return some output from a sample analysis export"""
    sample_analysis_output = {
        "ACC6987A15": {
            "snps": {
                "sequence": {
                    "rs10144418": ["T", "T"],
                    "rs1037256": ["G", "A"],
                    "rs1044973": ["C", "T"],
                    "rs1065772": ["C", "T"],
                    "rs11010": ["T", "C"],
                    "rs11789987": ["C", "T"],
                    "rs11797": ["C", "C"],
                }
            }
        },
        "ACC6987A16": {
            "snps": {
                "sequence": {
                    "rs10144418": ["T", "C"],
                    "rs1037256": ["G", "A"],
                    "rs1044973": ["C", "T"],
                    "rs1065772": ["C", "C"],
                    "rs11010": ["T", "T"],
                    "rs11789987": ["C", "T"],
                    "rs11797": ["T", "T"],
                }
            }
        },
    }
    return WriteStream.write_stream_from_content(
        content=sample_analysis_output, file_format=FileFormat.JSON
    )
