from pathlib import Path

import pytest

from cg.io.json import read_json
from cg.models.deliverables.metric_deliverables import MultiqcDataJson


@pytest.mark.parametrize(
    "multiqc_file_name",
    ("multiqc_data.json", "multiqc_data_new.json"),
    ids=["MultiQC <=1.28", "MultiQC >1.28"],
)
def test_parse_multiqc_json_old_version(multiqc_file_name: str, nallo_analysis_dir: Path):
    # GIVEN a MultiQC JSON file
    multiqc_path = Path(nallo_analysis_dir, multiqc_file_name)

    # WHEN parsing the JSON file into the MultiQC model
    multiqc = MultiqcDataJson(**read_json(file_path=multiqc_path))

    # THEN the report_general_stats is a list
    assert isinstance(multiqc.report_general_stats_data, list)
