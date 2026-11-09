from pathlib import Path

from cg.io.yaml import read_yaml


class StoreAnalysisService:
    def store_output(self, root_directory: Path, case_id: str):
        # TODO parse case_deliverables file
        # TODO go through the case directory, verify files' existence (?)
        # TODO create housekeeper bundle if successful, raise error otherwise

        # TODO find a better location for the definition of this path
        case_deliverables_file = Path(root_directory, case_id, f"{case_id}_deliverables.yaml")
        case_deliverables: list[dict] = read_yaml(case_deliverables_file)
