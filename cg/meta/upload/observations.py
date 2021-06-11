"""
    API for uploading observations
"""
from datetime import datetime
from pathlib import Path

import logging
from typing import List

from alchy import Query

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.loqus import LoqusdbAPI
from cg.constants.loqus_upload import ObservationAnalysisTag, ObservationAnalysisType
from cg.exc import CaseNotFoundError, DuplicateRecordError, DuplicateSampleError
from cg.models.observations.observations_input_files import ObservationsInputFiles
from cg.store import Store, models

LOG = logging.getLogger(__name__)


class UploadObservationsAPI:

    """API to upload observations to LoqusDB."""

    def __init__(self, status_api: Store, hk_api: HousekeeperAPI, loqus_api: LoqusdbAPI):
        self.status = status_api
        self.housekeeper = hk_api
        self.loqusdb = loqus_api

    def get_input(self, analysis_obj: models.Analysis) -> ObservationsInputFiles:
        """Fetch input files from an analysis to upload to observations"""

        analysis_date: datetime.datetime = analysis_obj.started_at or analysis_obj.completed_at
        hk_version: models.Version = self.housekeeper.version(
            analysis_obj.family.internal_id, analysis_date
        )

        hk_pedigree: Query = self.housekeeper.files(
            version=hk_version.id, tags=[ObservationAnalysisTag.PEDIGREE]
        ).first()
        hk_snv_gbcf: Query = self.housekeeper.files(
            version=hk_version.id, tags=[ObservationAnalysisTag.CHECK_PROFILE_GBCF]
        ).first()
        hk_snv_vcf: Query = self.housekeeper.files(
            version=hk_version.id, tags=[ObservationAnalysisTag.SNV_VARIANTS]
        ).first()
        sv_vcf_path = None
        if self.loqusdb.analysis_type == ObservationAnalysisType.WGS:
            hk_sv_vcf: Query = self.housekeeper.files(
                version=hk_version.id, tags=[ObservationAnalysisTag.SV_VARIANTS]
            ).first()
            sv_vcf_path: Path = hk_sv_vcf.full_path

        return ObservationsInputFiles(
            case_id=analysis_obj.family.internal_id,
            pedigree=hk_pedigree.full_path,
            snv_gbcf=hk_snv_gbcf.full_path,
            snv_vcf=hk_snv_vcf.full_path,
            sv_vcf=sv_vcf_path,
        )

    def upload(self, input_files: ObservationsInputFiles) -> None:
        """Upload data about genotypes for a family of samples."""

        try:
            existing_case = self.loqusdb.get_case(case_id=input_files.case_id)

        # If CaseNotFoundError is raised, this should trigger the load method of loqusdb
        except CaseNotFoundError:

            duplicate = self.loqusdb.get_duplicate(input_files.snv_gbcf)
            if duplicate:
                err_msg = f"Found duplicate {duplicate['ind_id']} in case {duplicate['case_id']}"
                raise DuplicateSampleError(err_msg)

            results = self.loqusdb.load(
                input_files.case_id,
                input_files.pedigree,
                input_files.snv_vcf,
                input_files.snv_gbcf,
                vcf_sv_path=input_files.sv_vcf,
            )
            LOG.info("parsed %s variants", results["variants"])

        else:
            log_msg = f"found existing family {existing_case['case_id']}, skipping observations"
            LOG.debug(log_msg)

    def process(self, analysis_obj: models.Analysis):
        """Process an upload observation counts for a case."""
        # check if some sample has already been uploaded
        for link in analysis_obj.family.links:
            if link.sample.loqusdb_id:
                raise DuplicateRecordError(f"{link.sample.internal_id} already in LoqusDB")
        results = self.get_input(analysis_obj)
        self.upload(results)
        case_obj = self.loqusdb.get_case(analysis_obj.family.internal_id)
        for link in analysis_obj.family.links:
            link.sample.loqusdb_id = str(case_obj["_id"])
        self.status.commit()

    @staticmethod
    def _all_samples(links: List[models.FamilySample]) -> bool:
        """Return True if all samples are external or sequenced inhouse."""
        return all((link.sample.sequenced_at or link.sample.is_external) for link in links)
