# -*- coding: utf-8 -*-
import logging

from cg.apps.tb import TrailblazerAPI
from cg.apps.hk import HousekeeperAPI
from cg.store import models, Store

log = logging.getLogger(__name__)


class AnalysisAPI():

    def __init__(self, db: Store, hk_api: HousekeeperAPI, tb_api: TrailblazerAPI):
        self.db = db
        self.tb = tb_api
        self.hk = hk_api

    def start(self, *args, **kwargs):
        """Start the analysis."""
        self.tb.start(*args, **kwargs)

    def config(self, family_obj: models.Family) -> dict:
        """Make the MIP config."""
        data = self.build_config(family_obj)
        config_data = self.tb.make_config(data)
        return config_data

    def build_config(self, family_obj: models.Family) -> dict:
        """Fetch data for creating a MIP config file."""
        data = {
            'family': family_obj.internal_id,
            'default_gene_panels': family_obj.panels,
            'samples': [],
        }
        for link in family_obj.links:
            sample_data = {
                'sample_id': link.sample.internal_id,
                'analysis_type': link.sample.application_version.application.category,
                'sex': link.sample.sex,
                'phenotype': link.status,
                'expected_coverage': link.sample.application_version.application.sequencing_depth,
            }
            if link.mother:
                sample_data['mother'] = link.mother.internal_id
            if link.father:
                sample_data['father'] = link.father.internal_id
            data['samples'].append(sample_data)
        return data

    def link_sample(self, link_obj: models.FamilySample):
        """Link FASTQ files for a sample."""
        file_objs = self.hk.files(bundle=link_obj.sample.internal_id, tags=['fastq'])
        files = [file_obj.path for file_obj in file_objs]
        self.tb.link(
            family=link_obj.family.internal_id,
            sample=link_obj.sample.internal_id,
            analysis_type=link_obj.sample.application_version.application.category,
            files=files,
        )
