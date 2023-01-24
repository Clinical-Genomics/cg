"""Handler to delete data objects"""

from typing import List
from cg.store.models import Flowcell, Family, FamilySample, Sample
from cg.store.api.base import BaseHandler


class DeleteDataHandler(BaseHandler):
    """Contains methods to delete business data model instances"""

    def delete_flowcell(self, flowcell_name: str):
        flowcell: Flowcell = self.Flowcell.query.filter(Flowcell.name == flowcell_name).first()
        if flowcell:
            flowcell.delete()
            flowcell.flush()
            self.commit()

    def delete_relationships_case(self, case: Family) -> None:
        """Delete association entries between a case and its samples."""
        for case_sample in case.links:
            case_sample.delete()
        self.commit()

    def delete_relationships_sample(self, sample: Sample):
        """Delete association between all cases and the provided sample."""
        for case_sample in sample.links:
            case_sample.delete()
        self.commit()

    def delete_cases_without_samples(self, case_ids: List[str]) -> List[str]:
        """Delete cases without samples."""
        for case_id in case_ids:
            case: Family = self.Family.query.filter(Family.internal_id == case_id).first()
            if not case.links:
                case.delete()
        self.commit()
