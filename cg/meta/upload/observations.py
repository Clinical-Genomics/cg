# -*- coding: utf-8 -*-
import logging

from cg.apps import hk, loqus
from cg.exc import DuplicateRecordError
from cg.store import models, Store

LOG = logging.getLogger(__name__)


class UploadObservationsAPI(object):

    """API to upload observations to LoqusDB."""

    def __init__(self, status_api: Store, hk_api: hk.HousekeeperAPI, loqus_api: loqus.LoqusdbAPI):
        self.status = status_api
        self.housekeeper = hk_api
        self.loqusdb = loqus_api

    def data(self, analysis_obj: models.Analysis) -> dict:
        """Fetch data about an analysis to load observations."""
        hk_version = self.housekeeper.version(analysis_obj.family.internal_id,
                                              analysis_obj.completed_at)
        hk_vcf = self.housekeeper.files(version=hk_version.id, tags=['vcf-snv-research']).first()
        hk_pedigree = self.housekeeper.files(version=hk_version.id, tags=['pedigree']).first()
        data = {
            'family': analysis_obj.family.internal_id,
            'vcf': str(hk_vcf.full_path),
            'pedigree': str(hk_pedigree.full_path),
        }
        return data

    def upload(self, data: dict):
        """Upload data about genotypes for a family of samples."""
        existing_case = self.loqusdb.case({'case_id': data['family']})
        if existing_case is None:
            results = self.loqusdb.load(data['family'], data['pedigree'], data['vcf'])
            LOG.info(f"parsed {results['variants']} variants")
        else:
            LOG.debug("found existing family, skipping observations")

    def process(self, analysis_obj: models.Analysis):
        """Process an upload observation counts for a case."""
        # check if some sample has already been uploaded
        for link in analysis_obj.family.links:
            if link.sample.loqusdb_id:
                raise DuplicateRecordError(f"{link.sample.internal_id} already in LoqusDB")
        results = self.data(analysis_obj)
        self.upload(results)
        case_obj = self.loqusdb.get_case(analysis_obj.family.internal_id)
        for link in analysis_obj.family.links:
            link.sample.loqusdb_id = str(case_obj['_id'])
        self.status.commit()
