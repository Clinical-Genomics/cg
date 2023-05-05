import logging
from pathlib import Path
from typing import List

from cgmodels.cg.constants import Pipeline

from cg.apps.gt import GenotypeAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.housekeeper.hk import models as housekeeper_models
from cg.constants.constants import FileFormat, PrepCategory
from cg.constants.housekeeper_tags import HkMipAnalysisTag
from cg.constants.subject import Gender
from cg.io.controller import ReadFile
from cg.models.mip.mip_metrics_deliverables import MIPMetricsDeliverables
from cg.store.models import Analysis, Family, Sample

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

    def data(self, analysis_obj: Analysis) -> dict:
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
        data = {"bcf": hk_bcf.full_path}
        if analysis_obj.pipeline in [Pipeline.BALSAMIC, Pipeline.BALSAMIC_UMI]:
            data["samples_sex"] = self._get_samples_sex_balsamic(case_obj=analysis_obj.family)
        elif analysis_obj.pipeline == Pipeline.MIP_DNA:
            data["samples_sex"] = self._get_samples_sex_mip(
                case_obj=analysis_obj.family, hk_version=hk_version
            )
        else:
            raise ValueError(f"Pipeline {analysis_obj.pipeline} does not support Genotype upload")
        return data

    def _get_samples_sex_mip(
        self, case_obj: Family, hk_version: housekeeper_models.Version
    ) -> dict:
        qc_metrics_file = self.get_qcmetrics_file(hk_version)
        analysis_sexes = self.analysis_sex(qc_metrics_file)
        samples_sex = {}
        for link_obj in case_obj.links:
            sample_id = link_obj.sample.internal_id
            samples_sex[sample_id] = {
                "pedigree": link_obj.sample.sex,
                "analysis": analysis_sexes[sample_id],
            }
        return samples_sex

    def _get_samples_sex_balsamic(self, case_obj: Family) -> dict:
        samples_sex = {}
        for link_obj in case_obj.links:
            if link_obj.sample.is_tumour:
                continue
            sample_id = link_obj.sample.internal_id
            samples_sex[sample_id] = {
                "pedigree": link_obj.sample.sex,
                "analysis": Gender.UNKNOWN,
            }
        return samples_sex

    def analysis_sex(self, qc_metrics_file: Path) -> dict:
        """Fetch analysis sex for each sample of an analysis."""
        qc_metrics: MIPMetricsDeliverables = self.get_parsed_qc_metrics_data(qc_metrics_file)
        return {
            sample_id_metric.sample_id: sample_id_metric.predicted_sex
            for sample_id_metric in qc_metrics.sample_id_metrics
        }

    def get_bcf_file(self, hk_version_obj: housekeeper_models.Version) -> housekeeper_models.File:
        """Fetch a bcf file and return the file object"""
        genotype_files: list = self._get_genotype_files(version_id=hk_version_obj.id)
        for genotype_file in genotype_files:
            if self._is_variant_file(genotype_file=genotype_file):
                LOG.debug("Found bcf file %s", genotype_file.full_path)
                return genotype_file
        raise FileNotFoundError(f"No vcf or bcf file found for bundle {hk_version_obj.bundle_id}")

    def get_qcmetrics_file(self, hk_version_obj: housekeeper_models.Version) -> Path:
        """Fetch a qc_metrics file and return the path"""
        hk_qcmetrics = self.hk.files(
            version=hk_version_obj.id, tags=HkMipAnalysisTag.QC_METRICS
        ).first()
        LOG.debug("Found qc metrics file %s", hk_qcmetrics.full_path)
        return Path(hk_qcmetrics.full_path)

    @staticmethod
    def get_parsed_qc_metrics_data(qc_metrics: Path) -> MIPMetricsDeliverables:
        """Parse the information from a qc metrics file"""
        qcmetrics_raw: dict = ReadFile.get_content_from_file(
            file_format=FileFormat.YAML, file_path=qc_metrics
        )
        return MIPMetricsDeliverables(**qcmetrics_raw)

    def upload(self, data: dict, replace: bool = False):
        """Upload data about genotypes for a family of samples."""
        self.gt.upload(str(data["bcf"]), data["samples_sex"], force=replace)

    @staticmethod
    def _is_variant_file(genotype_file: housekeeper_models.File):
        return genotype_file.full_path.endswith("vcf.gz") or genotype_file.full_path.endswith("bcf")

    def _get_genotype_files(self, version_id: int) -> list:
        return self.hk.files(version=version_id, tags=["genotype"]).all()

    @staticmethod
    def is_suitable_for_genotype_upload(case_obj: Family) -> bool:
        """Check if a cancer case is contains WGS and normal sample."""

        samples: List[Sample] = case_obj.samples
        return any(
            (not sample.is_tumour and PrepCategory.WHOLE_GENOME_SEQUENCING == sample.prep_category)
            for sample in samples
        )
