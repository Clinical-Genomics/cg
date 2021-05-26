"""
    conftest for genotype API
"""

import json

import pytest


@pytest.fixture(name="genotype_export_sample_output")
def fixture_genotype_export_sample_output(genotype_config: dict) -> str:
    """
    genotype API fixture
    """
    data = {
        "ACC6987A15": {
            "status": None,
            "sample_created_in_genotype_db": "2020-07-15",
            "sex": "female",
            "comment": None,
        },
        "ACC6987A16": {
            "status": None,
            "sample_created_in_genotype_db": "2020-07-15",
            "sex": "female",
            "comment": None,
        },
    }

    return json.dumps(data)


@pytest.fixture(name="genotype_export_sample_analysis_output")
def fixture_genotype_export_sample_analysis_output() -> str:
    """Return some output from a sample analysis export"""
    data = {
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
    return json.dumps(data)
