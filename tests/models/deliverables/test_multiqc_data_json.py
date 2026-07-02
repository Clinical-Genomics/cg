import json
from pathlib import Path
from typing import Type

import pytest

from cg.io.json import read_json
from cg.models.deliverables.metric_deliverables import MultiqcDataJson


@pytest.mark.parametrize(
    "multiqc_file_name",
    ("multiqc_data.json", "multiqc_data_new.json"),
    ids=["MultiQC <=1.28", "MultiQC >1.28"],
)
def test_parse_multiqc_json_success(multiqc_file_name: str, nallo_analysis_dir: Path):
    # GIVEN a MultiQC JSON file
    multiqc_path = Path(nallo_analysis_dir, multiqc_file_name)

    # WHEN parsing the JSON file into the MultiQC model
    multiqc = MultiqcDataJson(**read_json(file_path=multiqc_path))

    # THEN the report_general_stats is a list
    assert isinstance(multiqc.report_general_stats_data, list)


@pytest.mark.parametrize(
    "multiqc_json_stream, exception",
    [
        ('{"report_general_stats_data": "not_a_list"}', TypeError),
        ('{"report_data_sources": {}}', ValueError),
    ],
    ids=["Wrong format for report_general_stats_data", "Missing report_general_stats_data"],
)
def test_parse_multiqc_json_fail(multiqc_json_stream: str, exception: Type[BaseException]):
    # GIVEN a malformed MultiQC JSON file

    # WHEN trying to parse the JSON file into the MultiQC model
    # THEN an error is raised
    with pytest.raises(exception):
        MultiqcDataJson(**json.loads(multiqc_json_stream))
