import logging
from pathlib import Path

from housekeeper.store.models import File, Version

from cg.apps.gt import GenotypeAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.constants import FileFormat, PrepCategory, Workflow
from cg.constants.housekeeper_tags import HkMipAnalysisTag, RarediseaseAnalysisTag
from cg.constants.subject import Sex
from cg.io.controller import ReadFile
from cg.models.deliverables.metric_deliverables import MetricsBase
from cg.models.mip.mip_metrics_deliverables import MIPMetricsDeliverables
from cg.store.models import Analysis, Case, Sample

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

    def data(self, analysis: Analysis) -> dict:
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
        case_id = analysis.case.internal_id
        LOG.info(f"Fetching upload genotype data for {case_id}")
        hk_version = self.hk.last_version(case_id)
        hk_bcf = self.get_bcf_file(hk_version)
        data = {"bcf": hk_bcf.full_path}
        if analysis.workflow in [Workflow.BALSAMIC, Workflow.BALSAMIC_UMI]:
            data["samples_sex"] = self._get_samples_sex_balsamic(case_obj=analysis.case)
        elif analysis.workflow == Workflow.MIP_DNA:
            data["samples_sex"] = self._get_samples_sex_mip(
                case_obj=analysis.case, hk_version=hk_version
            )
        elif analysis.workflow == Workflow.RAREDISEASE:
            data["samples_sex"] = self._get_samples_sex_raredisease(
                case_obj=analysis.case, hk_version=hk_version
            )
        else:
            raise ValueError(f"Workflow {analysis.workflow} does not support Genotype upload")
        return data

    def _get_samples_sex_mip(self, case_obj: Case, hk_version: Version) -> dict:
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

    def _get_samples_sex_raredisease(self, case_obj: Case, hk_version: Version) -> dict:
        qc_metrics_file = self.get_qcmetrics_file_raredisease(hk_version)
        samples_sex = {}
        for link_obj in case_obj.links:
            sample_id = link_obj.sample.internal_id
            LOG.info(self.analysis_sex_raredisease(qc_metrics_file, sample_id=sample_id))
            samples_sex[sample_id] = {
                "pedigree": link_obj.sample.sex,
                "analysis": self.analysis_sex_raredisease(qc_metrics_file, sample_id=sample_id),
            }
        return samples_sex

    def _get_samples_sex_balsamic(self, case_obj: Case) -> dict:
        samples_sex = {}
        for link_obj in case_obj.links:
            if link_obj.sample.is_tumour:
                continue
            sample_id = link_obj.sample.internal_id
            samples_sex[sample_id] = {
                "pedigree": link_obj.sample.sex,
                "analysis": Sex.UNKNOWN,
            }
        return samples_sex

    def analysis_sex(self, qc_metrics_file: Path) -> dict:
        """Fetch analysis sex for each sample of an analysis."""
        qc_metrics: MIPMetricsDeliverables = self.get_parsed_qc_metrics_data_mip(qc_metrics_file)
        return {
            sample_id_metric.sample_id: sample_id_metric.predicted_sex
            for sample_id_metric in qc_metrics.sample_id_metrics
        }

    def analysis_sex_raredisease(self, qc_metrics_file: Path, sample_id: Sample) -> dict:
        """Fetch analysis sex for each sample of an analysis."""
        qc_metrics: list[MetricsBase] = self.get_parsed_qc_metrics_data_raredisease(qc_metrics_file)
        return str(next(metric.value for metric in qc_metrics if metric.name == "predicted_sex_sex_check" and metric.id == sample_id))

    def get_bcf_file(self, hk_version_obj: Version) -> File:
        """Fetch a bcf file and return the file object"""
        genotype_files: list = self._get_genotype_files(version_id=hk_version_obj.id)
        for genotype_file in genotype_files:
            if self._is_variant_file(genotype_file=genotype_file):
                LOG.debug(f"Found bcf file {genotype_file.full_path}")
                return genotype_file
        raise FileNotFoundError(f"No vcf or bcf file found for bundle {hk_version_obj.bundle_id}")

    def get_qcmetrics_file(self, hk_version_obj: Version) -> Path:
        """Fetch a qc_metrics file and return the path"""
        hk_qcmetrics = self.hk.files(
            version=hk_version_obj.id, tags=HkMipAnalysisTag.QC_METRICS
        ).first()
        LOG.debug(f"Found qc metrics file {hk_qcmetrics.full_path}")
        return Path(hk_qcmetrics.full_path)

    def get_qcmetrics_file_raredisease(self, hk_version_obj: Version) -> Path:
        """Fetch a qc_metrics file and return the path"""
        hk_qcmetrics = self.hk.files(
            version=hk_version_obj.id, tags=RarediseaseAnalysisTag.QC_METRICS
        ).first()
        LOG.info(f"Found qc metrics file {hk_qcmetrics.full_path}")
        return Path(hk_qcmetrics.full_path)

    @staticmethod
    def get_parsed_qc_metrics_data_mip(qc_metrics: Path) -> MIPMetricsDeliverables:
        """Parse the information from a qc metrics file"""
        qcmetrics_raw: dict = ReadFile.get_content_from_file(
            file_format=FileFormat.YAML, file_path=qc_metrics
        )
        return MIPMetricsDeliverables(**qcmetrics_raw)

    @staticmethod
    def get_parsed_qc_metrics_data_raredisease(qc_metrics: Path) -> MetricsBase:
        """Parse the information from a qc metrics file"""
        qcmetrics_raw: dict = ReadFile.get_content_from_file(
            file_format=FileFormat.YAML, file_path=qc_metrics
        )
        return [MetricsBase(**metric) for metric in qcmetrics_raw["metrics"]]

    def upload(self, data: dict, replace: bool = False):
        """Upload data about genotypes for a family of samples."""
        self.gt.upload(str(data["bcf"]), data["samples_sex"], force=replace)

    @staticmethod
    def _is_variant_file(genotype_file: File):
        return genotype_file.full_path.endswith("vcf.gz") or genotype_file.full_path.endswith("bcf")

    def _get_genotype_files(self, version_id: int) -> list:
        return self.hk.files(version=version_id, tags=["genotype"]).all()

    @staticmethod
    def is_suitable_for_genotype_upload(case_obj: Case) -> bool:
        """Check if a cancer case is contains WGS and normal sample."""

        samples: list[Sample] = case_obj.samples
        return any(
            (not sample.is_tumour and PrepCategory.WHOLE_GENOME_SEQUENCING == sample.prep_category)
            for sample in samples
        )
