from typing import List

import pytest


@pytest.fixture(name="deliverables_template_content")
def fixture_deliverables_template_content() -> List[dict]:
    return [
        {
            "format": "yml",
            "id": "CASEID",
            "path": "PATHTOCASE/pipeline_info/software_versions.yml",
            "path_index": None,
            "step": "software-versions",
            "tag": "software-versions",
        },
        {
            "format": "json",
            "id": "CASEID",
            "path": "PATHTOCASE/multiqc/multiqc_data/multiqc_data.json",
            "path_index": None,
            "step": "multiqc-json",
            "tag": "multiqc-json",
        },
    ]
