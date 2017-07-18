# -*- coding: utf-8 -*-
from cg.apps.tb import TrailblazerAPI
from cg.apps.stats import StatsAPI
from cg.store import models, Store


class AnalysisAPI():

    def __init__(self, db: Store, stats_api: StatsAPI, tb_api: TrailblazerAPI):
        self.db = db
        self.tb = tb_api
        self.stats = stats_api

    def config(self, family_obj: models.Family) -> dict:
        """Fetch data for creating a MIP config file."""
        data = {
            'family': family_obj.internal_id,
            'default_gene_panels': family_obj.panels,
            'samples': [{
                'sample_id': link.sample.internal_id,
                'analysis_type': link.sample.application_version.application.category,
                'sex': link.sample.sex,
                'phenotype': link.status,
                'mother': link.mother.internal_id if link.mother else None,
                'father': link.father.internal_id if link.father else None,
                'expected_coverage': link.sample.application_version.application.sequencing_depth,
            } for link in family_obj.links],
        }
        return data

    def link(self, family_obj: models.Family, dry: bool=False):
        """Link FASTQ files for all samples."""
        for link in family_obj.links:
            stats_sample = self.stats.sample(link.sample.internal_id)
            files = self.stats.fastqs(stats_sample)
            self.tb.link(
                family=family_obj.internal_id,
                sample=link.sample.internal_id,
                analysis_type=link.sample.application_version.application.category,
                files=files,
                dry=dry,
            )
