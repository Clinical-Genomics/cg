from pathlib import Path

from cg.constants.constants import MultiQC
from cg.services.multi_qc_parser import MultiQCParser
from cg.store.store import Store


def perform_qc(case_id: str, root_directory: Path, status_db: Store) -> None:

    # TODO: parse multiqc file using Pydantic
    multi_qc_parser = MultiQCParser(status_db)
    file = Path(root_directory, case_id, MultiQC.MULTIQC, MultiQC.MULTIQC_DATA, "multiqc_data.json")
    multi_qc_parser.parse_and_validate(file)

    # TODO: raise error if validation fails

    # TODO: add error comment to trailblazer

    pass
