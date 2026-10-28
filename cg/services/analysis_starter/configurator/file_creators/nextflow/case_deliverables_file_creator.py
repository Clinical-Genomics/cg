from pathlib import Path

from typing_extensions import Any

from cg.io.yaml import read_yaml, write_yaml
from cg.store.store import Store


class CaseDeliverablesFileCreator:
    def __init__(self, status_db: Store):
        self.status_db = status_db

    def create(
        self,
        case_id: str,
        case_directory: Path,
        file_path: Path,
        pipeline_deliverables: Path,
    ):
        """
        - read the pipeline deliverables file
        - in that content, replace all placeholders (e.g. SAMPLEID, CASEID, PATHTOCASE, et al)
        - for SAMPLEID, expand to one row for each sample in the case
        - write the result to file_path (analysis dir)
        """
        template: list[dict[str, Any]] = read_yaml(pipeline_deliverables)
        output = []
        for dictionary in template:
            replaced_dictionary = dictionary.copy()
            for key, value in dictionary.items():
                if isinstance(value, list):
                    replaced_dictionary[key] = [path.replace("CASEID", case_id) for path in value]
                elif isinstance(value, str):
                    replaced_dictionary[key] = value.replace("CASEID", case_id)
            output.append(replaced_dictionary)
        write_yaml(content=output, file_path=file_path)
