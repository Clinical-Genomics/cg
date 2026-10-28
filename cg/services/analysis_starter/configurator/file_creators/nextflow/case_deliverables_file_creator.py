from pathlib import Path

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
        - read the pipeline deliverables file
        - in that content, replace all placeholders (e.g. SAMPLEID, CASEID, PATHTOCASE, et al)
        - for SAMPLEID, expand to one row for each sample in the case
        - write the result to file_path (analysis dir)
        """
        pass
