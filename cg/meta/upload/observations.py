"""
    API for uploading observations
"""

from pathlib import Path
import logging
from typing import List

from cg.apps.hk import HousekeeperAPI
from cg.apps.loqus import LoqusdbAPI
from cg.exc import DuplicateRecordError, DuplicateSampleError, CaseNotFoundError
from cg.store import models, Store

LOG = logging.getLogger(__name__)


class UploadObservationsAPI:

    """API to upload observations to LoqusDB."""

    def __init__(self, status_api: Store, hk_api: HousekeeperAPI, loqus_api: LoqusdbAPI):
        self.status = status_api
        self.housekeeper = hk_api
        self.loqusdb = loqus_api

    def get_input(self, analysis_obj: models.Analysis) -> dict:
        """Fetch input data for an analysis to load observations."""

        input_data = {}

        analysis_date = analysis_obj.started_at or analysis_obj.completed_at
        hk_version = self.housekeeper.version(analysis_obj.family.internal_id, analysis_date)
        hk_vcf = self.housekeeper.files(version=hk_version.id, tags=["vcf-snv-research"]).first()
        hk_snv_gbcf = self.housekeeper.files(version=hk_version.id, tags=["snv-gbcf"]).first()
        hk_pedigree = self.housekeeper.files(version=hk_version.id, tags=["pedigree"]).first()

        input_data["sv_vcf"] = None
        if self.loqusdb.analysis_type == "wgs":
            hk_sv_vcf = self.housekeeper.files(
                version=hk_version.id, tags=["vcf-sv-research"]
            ).first()
            if hk_sv_vcf is None:
                raise FileNotFoundError("No file with vcf-sv-research tag in housekeeper")
            if not Path(hk_sv_vcf.full_path).exists():
                raise FileNotFoundError(f"{hk_sv_vcf.full_path} does not exist")
            input_data["sv_vcf"] = hk_sv_vcf.full_path

        hk_files = {"vcf-snv-research": hk_vcf, "snv-gbcf": hk_snv_gbcf, "pedigree": hk_pedigree}

        # Check if files exists. If hk returns None, or the path does not exist
        # FileNotFound error is raised
        for file_type, file in hk_files.items():
            if file is None:
                raise FileNotFoundError(f"No file with {file_type} tag in housekeeper")
            if not Path(file.full_path).exists():
                raise FileNotFoundError(f"{file.full_path} does not exist")

        input_data["family"] = analysis_obj.family.internal_id
        input_data["vcf"] = hk_vcf.full_path
        input_data["snv_gbcf"] = hk_snv_gbcf.full_path
        input_data["pedigree"] = hk_pedigree.full_path

        return input_data

    def upload(self, input_data: dict):
        """Upload data about genotypes for a family of samples."""

        try:
            existing_case = self.loqusdb.get_case(case_id=input_data["family"])

        # If CaseNotFoundError is raised, this should trigger the load method of loqusdb
        except CaseNotFoundError:

            duplicate = self.loqusdb.get_duplicate(input_data["snv_gbcf"])
            if duplicate:
                err_msg = f"Found duplicate {duplicate['ind_id']} in case {duplicate['case_id']}"
                raise DuplicateSampleError(err_msg)

            results = self.loqusdb.load(
                input_data["family"],
                input_data["pedigree"],
                input_data["vcf"],
                input_data["snv_gbcf"],
                vcf_sv_path=input_data["sv_vcf"],
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
