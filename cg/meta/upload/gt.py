import logging
from pathlib import Path

import yaml
from cg.apps.gt import GenotypeAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.housekeeper.hk import models as housekeeper_models
from cg.constants.tags import HkMipAnalysisTag
from cg.models.mip.mip_metrics_deliverables import MetricsDeliverables
from cg.store import models

LOG = logging.getLogger(__name__)


class UploadGenotypesAPI(object):
    def __init__(
        self,
        hk_api: HousekeeperAPI,
        gt_api: GenotypeAPI,
    ):
        LOG.info("Initializing UploadGenotypesAPI")
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
        case_id = analysis_obj.family.internal_id
        LOG.info("Fetching upload genotype data for %s", case_id)
        hk_version = self.hk.last_version(case_id)
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
        qc_metrics: MetricsDeliverables = self.get_parsed_qc_metrics_data(qc_metrics_file)
        return {
            sample_id_metric.sample_id: sample_id_metric.predicted_sex
            for sample_id_metric in qc_metrics.sample_id_metrics
        }

    def get_bcf_file(self, hk_version_obj: housekeeper_models.Version) -> housekeeper_models.File:
        """Fetch a bcf file and return the file object"""

        bcf_file = self.hk.files(version=hk_version_obj.id, tags=["snv-gbcf"]).first()
        LOG.debug("Found bcf file %s", bcf_file.full_path)
        return bcf_file

    def get_qcmetrics_file(self, hk_version_obj: housekeeper_models.Version) -> Path:
        """Fetch a qc_metrics file and return the path"""
        hk_qcmetrics = self.hk.files(
            version=hk_version_obj.id, tags=[HkMipAnalysisTag.QC_METRICS]
        ).first()
        LOG.debug("Found qc metrics file %s", hk_qcmetrics.full_path)
        return Path(hk_qcmetrics.full_path)

    @staticmethod
    def get_parsed_qc_metrics_data(qc_metrics: Path) -> MetricsDeliverables:
        """Parse the information from a qc metrics file"""
        with qc_metrics.open() as in_stream:
            qcmetrics_raw = yaml.safe_load(in_stream)
        return MetricsDeliverables(**qcmetrics_raw)

    def upload(self, data: dict, replace: bool = False):
        """Upload data about genotypes for a family of samples."""
        self.gt.upload(str(data["bcf"]), data["samples_sex"], force=replace)
