# -*- coding: utf-8 -*-
from cg.store import models


class AnalysisHandler:

    def config(self, family_obj: models.Family) -> dict:
        """Fetch data for creating a MIP config file."""
        data = {
            'family': family_obj.internal_id,
            'samples': [{
                'sample_id': sample_obj.sample.internal_id,
                'sex': sample_obj.sample.sex,
                'phenotype': sample_obj.status,
                'mother': sample_obj.mother.internal_id if sample_obj.mother else None,
                'father': sample_obj.father.internal_id if sample_obj.father else None,
            } for sample_obj in family_obj.samples],
        }
        return data
