from pathlib import Path

from typing_extensions import Any

from cg.io.yaml import read_yaml, write_yaml
from cg.store.models import Case, Sample
from cg.store.store import Store


class CaseDeliverablesFileCreator:
    def __init__(self, status_db: Store):
        self.status_db = status_db

    def _fill_placeholders(self, input_str: str, case_dir: Path, case: Case, sample: Sample | None):
        replacements = {
            "PATHTOCASE": case_dir,
            "CASEID": case.internal_id,
        }
        if sample:
            replacements.update(
                {
                    "SAMPLEID": sample.internal_id,
                    "SAMPLENAME": sample.name,
                }
            )

        output = input_str
        for placeholder, value in replacements.items():
            output = output.replace(placeholder, str(value))

        return output

    def _make_filetype_dict(
        self, template: dict, case_directory: Path, case: Case, sample: Sample | None
    ) -> dict:
        new_dict = {}
        for key, value in template.items():
            if isinstance(value, str):
                new_dict[key] = self._fill_placeholders(
                    value, case_dir=case_directory, case=case, sample=sample
                )
            elif isinstance(value, list):
                new_dict[key] = [
                    self._fill_placeholders(
                        input_str=path, case_dir=case_directory, case=case, sample=sample
                    )
                    for path in value
                ]
            else:
                new_dict[key] = template[key]
        return new_dict

    def create(
        self,
        case_id: str,
        case_directory: Path,
        file_path: Path,
        pipeline_deliverables: Path,
    ):
        template: list[dict[str, Any]] = read_yaml(pipeline_deliverables)
        result: list[dict] = []

        case: Case = self.status_db.get_case_by_internal_id_strict(case_id)
        samples: list[Sample] = case.samples

        for file_type in template:
            if file_type["id"] == "SAMPLEID":
                for sample in samples:
                    result.append(
                        self._make_filetype_dict(
                            template=file_type,
                            case_directory=case_directory,
                            case=case,
                            sample=sample,
                        )
                    )
            else:
                result.append(
                    self._make_filetype_dict(
                        template=file_type,
                        case_directory=case_directory,
                        case=case,
                        sample=None,
                    )
                )

        write_yaml(content=result, file_path=file_path)
