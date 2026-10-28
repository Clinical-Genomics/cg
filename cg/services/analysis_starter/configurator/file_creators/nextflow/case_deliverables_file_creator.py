from pathlib import Path

from typing_extensions import Any

from cg.io.yaml import read_yaml, write_yaml
from cg.store.models import Case
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
        output: list[dict] = []
        case: Case = self.status_db.get_case_by_internal_id_strict(case_id)
        case_replacements = {"CASEID": case.internal_id, "PATHTOCASE": case_directory.as_posix()}
        for file_type_dict in template:
            if file_type_dict["id"] == "SAMPLEID":
                for sample in case.samples:
                    sample_replacements = {
                        **case_replacements,
                        "SAMPLENAME": sample.name,
                        "SAMPLEID": sample.internal_id,
                    }
                    output.append(
                        self._get_new_dict(
                            old_dict=file_type_dict, replacements=sample_replacements
                        )
                    )
            else:
                output.append(
                    self._get_new_dict(old_dict=file_type_dict, replacements=case_replacements)
                )
        write_yaml(content=output, file_path=file_path)

    def _get_new_dict(self, old_dict: dict, replacements: dict):
        return {key: self._get_new_value(value, replacements) for key, value in old_dict.items()}

    def _get_new_value(self, old_value: Any, replacements: dict):
        match old_value:
            case bool():
                return old_value
            case str():
                return self.replace(old_value, replacements)
            case list():
                return [self.replace(path, replacements) for path in old_value]
            case _:
                raise NotImplementedError(
                    f"Unknown format of pipeline deliverables file, value {old_value}"
                )

    @staticmethod
    def replace(string: str, replacements: dict):
        for old_value, new_value in replacements.items():
            string = string.replace(old_value, new_value)
        return string
