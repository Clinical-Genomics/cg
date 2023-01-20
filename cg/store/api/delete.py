"""Handler to delete data objects"""

from typing import List
from cg.store.models import Flowcell, Family, FamilySample
from cg.store.api.base import BaseHandler


class DeleteDataHandler(BaseHandler):
    """Contains methods to delete business data model instances"""

    def delete_flowcell(self, flowcell_name: str):
        flowcell: Flowcell = self.Flowcell.query.filter(Flowcell.name == flowcell_name).first()
        if flowcell:
            flowcell.delete()
            flowcell.flush()
            self.commit()

    def delete_case(self, case_id: str) -> None:
        """Delete a case and all associations with samples."""
        self.delete_all_case_sample_relationships(case_id=case_id)
        case: Family = self.Family.query.filter(Family.internal_id == case_id).first()
        if case:
            case.delete()
            case.flush()
            self.commit()

    def delete_all_case_sample_relationships(self, case_id: str) -> None:
        """Delete association entries between a case and its samples."""
        case_samples: List[FamilySample] = (
            self.FamilySample.query.join(FamilySample.family, FamilySample.sample)
            .filter(Family.internal_id == case_id)
            .all()
        )
        if case_samples:
            for case_sample in case_samples:
                case_sample.delete()
                case_sample.flush()
            self.commit()

    def delete_case_sample_relationships(self, sample_entry_id: int):
        """Delete association between all cases and the provided sample."""
        case_samples: List[FamilySample] = self.FamilySample.query.filter(
            self.Sample.id == sample_entry_id
        ).all()
        if case_samples:
            for case_sample in case_samples:
                case_sample.delete()
                case_sample.flush()
            self.commit()

    def delete_cases_without_samples(self, case_ids) -> List[str]:
        """Delete cases without samples."""
        for case_id in case_ids:
            case: Family = self.Family.query.filter(Family.internal_id == case_id).first()
            if not case.samples:
                self.delete_case(case_id)
