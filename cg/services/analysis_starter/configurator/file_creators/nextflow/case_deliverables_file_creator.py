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
        result: list[dict] = []

        case: Case = self.status_db.get_case_by_internal_id_strict(case_id)
        case_replacements = {"CASEID": case.internal_id, "PATHTOCASE": case_directory.as_posix()}

        for file_type_dict in template:
            replaced_dictionary = {}
            if file_type_dict["id"] == "SAMPLEID":
                for sample in case.samples:
                    sample_replacements = {
                        **case_replacements,
                        "SAMPLENAME": sample.name,
                        "SAMPLEID": sample.internal_id,
                    }
                    result.append(
                        self._transform_dict(old_dict=file_type_dict, replacements=sample_replacements))
            else:
                result.append(self._transform_dict(old_dict=file_type_dict, replacements=case_replacements))




                """-----"""
                for sample in samples:
                    sample_dict = {}
                    for key, value in file_type_dict.items():
                        if isinstance(value, str):
                            sample_dict[key] = (
                                file_type_dict[key]
                                .replace("SAMPLENAME", sample.name)
                                .replace("SAMPLEID", sample.internal_id)
                                .replace("CASEID", case.internal_id)
                                .replace("PATHTOCASE", case_directory.as_posix())
                            )
                        elif isinstance(value, list):
                            new_paths: list[str] = []
                            for path in value:
                                new_paths.append(
                                    path.replace("SAMPLENAME", sample.name)
                                    .replace("SAMPLEID", sample.internal_id)
                                    .replace("CASEID", case.internal_id)
                                    .replace("PATHTOCASE", case_directory.as_posix())
                                )
                            sample_dict[key] = new_paths
                        else:
                            sample_dict[key] = value
                    output.append(sample_dict)
            else:
                case_dict = {}
                for key, value in file_type_dict.items():
                    if isinstance(value, list):
                        case_dict[key] = [
                            path.replace("CASEID", case_id).replace(
                                "PATHTOCASE", str(case_directory)
                            )
                            for path in value
                        ]
                    elif isinstance(value, str):
                        case_dict[key] = value.replace("CASEID", case_id).replace(
                            "PATHTOCASE", str(case_directory)
                        )
                    else:
                        case_dict[key] = value
                output.append(case_dict)
        write_yaml(content=output, file_path=file_path)


"""
            for key, value in dictionary.items():
                if isinstance(value, str):
                    if "SAMPLEID" in value or "SAMPLENAME" in value:
                        for sample in samples:
                            sample_dict = {}
            for key, value in dictionary.items():
                if isinstance(value, list):
                    replaced_dictionary[key] = [
                        path.replace("CASEID", case_id).replace("PATHTOCASE", str(case_directory))
                        for path in value
                    ]
                elif isinstance(value, str):
                    replaced_dictionary[key] = value.replace("CASEID", case_id).replace(
                        "PATHTOCASE", str(case_directory)
                    )
            output.append(replaced_dictionary)
"""
