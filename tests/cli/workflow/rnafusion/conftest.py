from pathlib import Path
from typing import List

import pytest

from cg.constants import FileExtensions


@pytest.fixture(name="deliverables_template_content", scope="session")
def fixture_deliverables_template_content() -> List[dict]:
    return [
        {
            "format": "yml",
            "id": "CASEID",
            "path": Path("PATHTOCASE", "pipeline_info", "software_versions.yml").as_posix(),
            "path_index": None,
            "step": "software-versions",
            "tag": "software-versions",
        },
        {
            "format": "json",
            "id": "CASEID",
            "path": Path("PATHTOCASE", "multiqc", "multiqc_data", "multiqc_data")
            .with_suffix(FileExtensions.JSON)
            .as_posix(),
            "path_index": None,
            "step": "multiqc-json",
            "tag": "multiqc-json",
        },
    ]
