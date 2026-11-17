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
        Create a deliverables file for the given case, based on the provided pipeline deliverables template.
        The process involves:
        - read the pipeline deliverables template file
        - replace all placeholders (e.g. SAMPLEID, SAMPLENAME, CASEID, and PATHTOCASE) with correct values
        - for sections containing sample information, expand to one entry per sample in the case
        - write the result to file_path located in the case analysis directory
        """
        template: list[dict[str, Any]] = read_yaml(pipeline_deliverables)
        content: list[dict] = []

        case: Case = self.status_db.get_case_by_internal_id_strict(case_id)
        case_replacements = {"CASEID": case.internal_id, "PATHTOCASE": file_path.parent.as_posix()}

        for file_type_dict in template:
            if file_type_dict["id"] == "SAMPLEID":  # TODO: We have to revise if this applies
                content.extend(
                    self._create_transformed_sample_dicts(
                        samples=case.samples,
                        file_type_dict=file_type_dict,
                        case_replacements=case_replacements,
                    )
                )
            else:
                content.append(
                    self._transform_dict(old_dict=file_type_dict, replacements=case_replacements)
                )
        write_yaml(content=content, file_path=file_path)

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
