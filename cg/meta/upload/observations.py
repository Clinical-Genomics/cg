# -*- coding: utf-8 -*-

"""
    API for uploading observations
"""

import logging
from typing import List

from cg.apps import hk, loqus
from cg.exc import DuplicateRecordError, DuplicateSampleError, CaseNotFoundError
from cg.store import models, Store

LOG = logging.getLogger(__name__)


class UploadObservationsAPI():

    """API to upload observations to LoqusDB."""

    def __init__(self, status_api: Store, hk_api: hk.HousekeeperAPI, loqus_api: loqus.LoqusdbAPI):
        self.status = status_api
        self.housekeeper = hk_api
        self.loqusdb = loqus_api

    def data(self, analysis_obj: models.Analysis) -> dict:
        """Fetch data about an analysis to load observations."""
        analysis_date = analysis_obj.started_at or analysis_obj.completed_at
        hk_version = self.housekeeper.version(analysis_obj.family.internal_id, analysis_date)
        hk_vcf = self.housekeeper.files(version=hk_version.id, tags=['vcf-snv-research']).first()
        hk_sv_vcf = self.housekeeper.files(version=hk_version.id, tags=['vcf-sv-research']).first()
        hk_snv_gbcf = self.housekeeper.files(version=hk_version.id, tags=['snv-gbcf']).first()
        hk_pedigree = self.housekeeper.files(version=hk_version.id, tags=['pedigree']).first()
        data = {
            'family': analysis_obj.family.internal_id,
            'vcf': str(hk_vcf.full_path),
            'sv_vcf': str(hk_sv_vcf.full_path),
            'snv_gbcf': str(hk_snv_gbcf.full_path),
            'pedigree': str(hk_pedigree.full_path),
        }
        return data

    def upload(self, data: dict):
        """Upload data about genotypes for a family of samples."""

        try:
            existing_case = self.loqusdb.get_case(case_id=data['family'])

        # If CaseNotFoundError is raised, this should trigger the load method of loqusdb
        except CaseNotFoundError:

            duplicate = self.loqusdb.get_duplicate(data['snv_gbcf'])
            if duplicate:
                err_msg = f"Found duplicate {duplicate['ind_id']} in case {duplicate['case_id']}"
                raise DuplicateSampleError(err_msg)

            results = self.loqusdb.load(data['family'], data['pedigree'], data['vcf'],
                                        data['sv_vcf'], data['snv_gbcf'])
            log_msg = f"parsed {results['variants']} variants"
            LOG.info(log_msg)

        else:
            log_msg = f"found existing family {existing_case['case_id']}, skipping observations"
            LOG.debug(log_msg)

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

    @staticmethod
    def _all_samples(links: List[models.FamilySample]) -> bool:
        """Return True if all samples are external or sequenced inhouse."""
        return all((link.sample.sequenced_at or link.sample.is_external) for link in links)
