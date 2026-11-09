from collections.abc import Iterator
from pathlib import Path

from cg.io.json import read_json
from cg.meta.workflow.nf_analysis import MultiQCSearchPattern
from cg.models.deliverables.metric_deliverables import MultiqcDataJson
from cg.store.store import Store


class MultiQCParser:
    def __init__(self, status_db: Store) -> None:
        self.status_db = status_db

    def parse_and_validate(self, file: Path) -> None:
        multiqc_model = MultiqcDataJson(**read_json(file_path=file))

    def _get_multiqc_search_patterns(self, case_id: str) -> list[MultiQCSearchPattern]:
        # TODO simplify this method to avoid the MultiQCSearchPattern
        """Return a list of MultiQC search patterns for a case.
        Each pattern pairs a search string with its corresponding sample ID.
        Search patterns are typically sample IDs used to extract metrics from MultiQC data."""
        sample_ids: Iterator[str] = self.status_db.get_sample_ids_by_case_id(case_id)
        return [
            MultiQCSearchPattern(pattern=sample_id, sample_id=sample_id) for sample_id in sample_ids
        ]
