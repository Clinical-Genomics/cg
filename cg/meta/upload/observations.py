# -*- coding: utf-8 -*-
import logging

from cg.apps import hk, loqus
from cg.store import models, Store

log = logging.getLogger(__name__)


class UploadObservationsAPI(object):

    def __init__(self, status_api: Store, hk_api: hk.HousekeeperAPI, loqus_api: loqus.LoqusdbAPI):
        self.status = status_api
        self.hk = hk_api
        self.loqus = loqus_api

    def data(self, analysis_obj: models.Analysis) -> dict:
        """Fetch data about an analysis to load observations."""
        hk_version = self.hk.version(analysis_obj.family.internal_id, analysis_obj.completed_at)
        hk_vcf = self.hk.files(version=hk_version.id, tags=['vcf-snv-research']).first()
        hk_pedigree = self.hk.files(version=hk_version.id, tags=['pedigree']).first()
        data = {
            'family': analysis_obj.family.internal_id,
            'vcf': hk_vcf.full_path,
            'pedigree': hk_pedigree.full_path,
        }
        return data

    def upload(self, data: dict):
        """Upload data about genotypes for a family of samples."""
        results = self.loqus.load(data['family'], data['pedigree'], data['vcf'])
        log.info(f"inserted {results['inserted']} / {results['variants']} variants")
