# -*- coding: utf-8 -*-
import logging

from cg.apps import hk, scoutapi
from cg.store import models, Store
from cg.meta.analysis import AnalysisAPI

LOG = logging.getLogger(__name__)


class UploadScoutAPI(object):

    def __init__(self, status_api: Store, hk_api: hk.HousekeeperAPI, scout_api: scoutapi.ScoutAPI):
        self.status = status_api
        self.housekeeper = hk_api
        self.scout = scout_api

    def data(self, analysis_obj: models.Analysis) -> dict:
        """Fetch data about an analysis to load Scout."""
        hk_version = self.housekeeper.version(analysis_obj.family.internal_id,
                                              analysis_obj.completed_at)

        data = {
            'owner': analysis_obj.family.customer.internal_id,
            'family': analysis_obj.family.internal_id,
            'family_name': analysis_obj.family.name,
            'samples': [{
                'analysis_type': None,
                'sample_id': link_obj.sample.internal_id,
                'capture_kit': None,
                'father': link_obj.father.internal_id if link_obj.father else None,
                'mother': link_obj.mother.internal_id if link_obj.mother else None,
                'sample_name': link_obj.sample.name,
                'phenotype': link_obj.status,
                'sex': link_obj.sample.sex,
            } for link_obj in analysis_obj.family.links],
            'analysis_date': analysis_obj.completed_at,
            'gene_panels': AnalysisAPI.convert_panels(analysis_obj.family.customer.internal_id,
                                                      analysis_obj.family.panels),
            'default_gene_panels': analysis_obj.family.panels,
        }

        files = {('vcf_snv', 'vcf-snv-clinical'), ('vcf_snv_research', 'vcf-snv-research'),
                 ('vcf_sv', 'vcf-sv-clinical'), ('vcf_sv_research', 'vcf-sv-research')}
        for scout_key, hk_tag in files:
            hk_vcf = self.housekeeper.files(version=hk_version.id, tags=[hk_tag]).first()
            data[scout_key] = str(hk_vcf.full_path)

        return data
