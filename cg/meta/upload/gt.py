import logging
from pathlib import Path

import ruamel.yaml

from cg.apps import hk, gt
from cg.store import models
from cg.apps.tb.api import TrailblazerAPI

LOG = logging.getLogger(__name__)


class UploadGenotypesAPI(object):
    def __init__(
        self,
        hk_api: hk.HousekeeperAPI,
        gt_api: gt.GenotypeAPI,
    ):
        self.hk = hk_api
        self.gt = gt_api

    def data(self, analysis_obj: models.Analysis) -> dict:
        """Fetch data about an analysis to load genotypes.

        Returns: dict on form

        {
            "bcf": path_to_bcf,
            "samples_sex": [
                "sample_id: {
                    "pedigree": "male",
                    "analysis": "male"
                    }
            ]
        }

        """
        analysis_date = analysis_obj.started_at or analysis_obj.completed_at
        hk_version = self.hk.version(analysis_obj.family.internal_id, analysis_date)
        hk_bcf = self.get_bcf_file(hk_version)
        if hk_bcf is None:
            LOG.warning("unable to find GBCF for genotype upload")
            return None
        data = {"bcf": hk_bcf.full_path, "samples_sex": {}}
        qc_metrics_file = self.get_qcmetrics_file(hk_version)
        analysis_sexes = self.analysis_sex(qc_metrics_file)
        for link_obj in analysis_obj.family.links:
            sample_id = link_obj.sample.internal_id
            data["samples_sex"][sample_id] = {
                "pedigree": link_obj.sample.sex,
                "analysis": analysis_sexes[sample_id],
            }
        return data

    def analysis_sex(self, qc_metrics_file: Path) -> dict:
        """Fetch analysis sex for each sample of an analysis."""
        qcmetrics_data = self.get_parsed_qc_metrics_data(qc_metrics_file)
        samples = [sample["id"] for sample in qcmetrics_data["samples"]]
        data = {}
        for sample_id in samples:
            data[sample_id] = self.get_sample_predicted_sex(
                sample_id=sample_id, parsed_qcmetrics_data=qcmetrics_data
            )
        return data

    def get_bcf_file(self, hk_version_obj: hk.models.Version) -> hk.models.File:
        """Fetch a bcf file and return the file object"""

        bcf_file = self.hk.files(version=hk_version_obj.id, tags=["snv-gbcf"]).first()
        LOG.debug("Found bcf file %s", bcf_file.full_path)
        return bcf_file

    def get_qcmetrics_file(self, hk_version_obj: hk.models.Version) -> Path:
        """Fetch a qc_metrics file and return the path"""
        hk_qcmetrics = self.hk.files(version=hk_version_obj.id, tags=["qcmetrics"]).first()
        LOG.debug("Found qc metrics file %s", hk_qcmetrics.full_path)
        return Path(hk_qcmetrics.full_path)

    @staticmethod
    def get_parsed_qc_metrics_data(qc_metrics: Path) -> dict:
        """Parse the information from a qc metrics file"""
        with qc_metrics.open() as in_stream:
            qcmetrics_raw = ruamel.yaml.safe_load(in_stream)
        return TrailblazerAPI.parse_qcmetrics(qcmetrics_raw)

    @staticmethod
    def get_sample_predicted_sex(sample_id: str, parsed_qcmetrics_data: dict) -> str:
        """Get the predicted sex for a sample"""
        predicted_sex = "unknown"
        for sample_info in parsed_qcmetrics_data["samples"]:
            if sample_info["id"] == sample_id:
                return sample_info["predicted_sex"]

        return predicted_sex

    def upload(self, data: dict, replace: bool = False):
        """Upload data about genotypes for a family of samples."""
        self.gt.upload(str(data["bcf"]), data["samples_sex"], force=replace)
