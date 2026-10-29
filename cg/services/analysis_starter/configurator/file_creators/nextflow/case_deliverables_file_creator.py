from pathlib import Path

from typing_extensions import Any

from cg.io.yaml import read_yaml, write_yaml
from cg.store.models import Case, Sample
from cg.store.store import Store


class CaseDeliverablesFileCreator:
    def __init__(self, status_db: Store):
        self.status_db = status_db

    def create(
        self,
        case_id: str,
        file_path: Path,
        pipeline_deliverables: Path,
    ):
        """
        TODO refine docstring
        - read the pipeline deliverables file
        - in that content, replace all placeholders (e.g. SAMPLEID, CASEID, PATHTOCASE, et al)
        - for SAMPLEID, expand to one row for each sample in the case
        - write the result to file_path (analysis dir)
        """
        template: list[dict[str, Any]] = read_yaml(pipeline_deliverables)
        result: list[dict] = []

        case: Case = self.status_db.get_case_by_internal_id_strict(case_id)
        case_directory: Path = file_path.parent
        case_replacements = {"CASEID": case.internal_id, "PATHTOCASE": case_directory.as_posix()}

        for file_type_dict in template:
            if file_type_dict["id"] == "SAMPLEID":
                result.extend(
                    self._create_transformed_sample_dicts(
                        samples=case.samples,
                        file_type_dict=file_type_dict,
                        case_replacements=case_replacements,
                    )
                )
            else:
                result.append(
                    self._transform_dict(old_dict=file_type_dict, replacements=case_replacements)
                )
        write_yaml(content=result, file_path=file_path)

    def _create_transformed_sample_dicts(
        self, samples: list[Sample], file_type_dict: dict, case_replacements: dict
    ) -> list[dict]:
        sample_dicts: list[dict] = []
        for sample in samples:
            sample_replacements = {
                **case_replacements,
                "SAMPLENAME": sample.name,
                "SAMPLEID": sample.internal_id,
            }
            sample_dicts.append(
                self._transform_dict(old_dict=file_type_dict, replacements=sample_replacements)
            )
        return sample_dicts

    def _transform_dict(self, old_dict: dict, replacements: dict) -> dict:
        return {
            key: self._get_new_value(old_value=old_value, replacements=replacements)
            for key, old_value in old_dict.items()
        }

    def _get_new_value(self, old_value: Any, replacements: dict):
        match old_value:
            case str():
                return self._replace_placeholders(string=old_value, replacements=replacements)
            case list():
                return [
                    self._replace_placeholders(string=path, replacements=replacements)
                    for path in old_value
                ]
            case _:
                return old_value

    @staticmethod
    def _replace_placeholders(string: str, replacements: dict[str, str]):
        for placeholder, value in replacements.items():
            string = string.replace(placeholder, value)
        return string
