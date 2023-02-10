"""Handler to delete data objects"""

from typing import List
from cg.store.models import Flowcell, Family, Sample
from cg.store.api.base import BaseHandler


class DeleteDataHandler(BaseHandler):
    """Contains methods to delete business data model instances"""

    def delete_flow_cell(self, flow_cell_name: str) -> None:
        """Delete flow cell."""
        flow_cell: Flowcell = self.Flowcell.query.filter(Flowcell.name == flow_cell_name).first()

        if flow_cell:
            flow_cell.delete()
            flow_cell.flush()
            self.commit()

    def delete_relationships_sample(self, sample: Sample) -> None:
        """Delete relationships between all cases and the provided sample."""
        if sample and sample.links:
            for case_sample in sample.links:
                case_sample.delete()
            self.commit()

    def delete_cases_without_samples(self, case_ids: List[str]) -> None:
        """Delete any cases specified in case_ids without samples."""
        for case_id in case_ids:
            case: Family = self.Family.query.filter(Family.internal_id == case_id).first()
            if case and not case.links:
                case.delete()
        self.commit()
