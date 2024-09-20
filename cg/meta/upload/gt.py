import logging
from pathlib import Path

from cg.apps.gt import GenotypeAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.constants import FileFormat, PrepCategory, Workflow
from cg.constants.housekeeper_tags import GenotypeAnalysisTag, HkAnalysisMetricsTag
from cg.constants.nf_analysis import RAREDISEASE_PREDICTED_SEX_METRIC
from cg.constants.subject import Sex
from cg.io.controller import ReadFile
from cg.models.deliverables.metric_deliverables import MetricsBase
from cg.models.mip.mip_metrics_deliverables import MIPMetricsDeliverables

from cg.store.models import Analysis, Case, Sample

from housekeeper.store.models import File, Version

LOG = logging.getLogger(__name__)


class UploadGenotypesAPI(object):
    """Genotype upload API."""

    def __init__(
        self,
        hk_api: HousekeeperAPI,
        gt_api: GenotypeAPI,
    ):
        LOG.info("Initializing UploadGenotypesAPI")
        self.hk = hk_api
        self.gt = gt_api

    def get_genotype_data(self, case: Case) -> dict[dict[str, dict[str, str]]]:
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
        LOG.info(f"workflow: {case.data_analysis}")
        case_id = case.internal_id
        LOG.info(f"Fetching upload genotype data for {case_id}")
        hk_version: Version = self.hk.last_version(bundle=case_id)

        hk_bcf = self.get_bcf_file(case_id=case_id)

        gt_data: dict = {"bcf": hk_bcf.full_path}
        if case.data_analysis in [Workflow.BALSAMIC, Workflow.BALSAMIC_UMI]:
            gt_data["samples_sex"] = self.get_samples_sex_balsamic(case=case)
        elif case.data_analysis == Workflow.MIP_DNA:
            gt_data["samples_sex"] = self.get_samples_sex_mip_dna(case=case, hk_version=hk_version)
        elif case.data_analysis == Workflow.RAREDISEASE:
            gt_data["samples_sex"] = self.get_samples_sex_raredisease(
                case=case, hk_version=hk_version
            )
        else:
            raise ValueError(f"Workflow {case.data_analysis} does not support Genotype upload")
        return gt_data

    def upload(self, gt_data: dict, replace: bool = False):
        """Upload data about genotypes for a family of samples."""
        self.gt.upload(str(gt_data["bcf"]), gt_data["samples_sex"], force=replace)

    @staticmethod
    def is_suitable_for_genotype_upload(case: Case) -> bool:
        """Check if a cancer case is contains WGS and normal sample."""

        samples: list[Sample] = case.samples
        return any(
            (not sample.is_tumour and PrepCategory.WHOLE_GENOME_SEQUENCING == sample.prep_category)
            for sample in samples
        )

    def get_genotype_file(self, case_id: str) -> File:
        tags: set[str] = {GenotypeAnalysisTag.GENOTYPE}
        hk_genotype = self.hk.get_file_from_latest_version(bundle_name=case_id, tags=tags)
        if not hk_genotype:
            raise FileNotFoundError(f"Genotype file not found for {case_id}")
        LOG.info(f"Found genotype file {hk_genotype.full_path}")


    def is_variant_file(self, genotype_file: File):
        return genotype_file.full_path.endswith("vcf.gz") or genotype_file.full_path.endswith("bcf")

    def get_bcf_file(
        self,
        case_id: str,
    ) -> File:
        """Return a BCF file object. Raises error if nothing is found in the bundle"""
        LOG.debug("Get genotype files from Housekeeper")
        genotype_file=self.get_genotype_file(case_id=case_id)
        if self.is_variant_file(genotype_file=genotype_file):
            LOG.debug(f"Found BCF file {genotype_file.full_path}")
            return genotype_file
        raise FileNotFoundError(f"No VCF or BCF file found for the last bundle of {case_id}")

    def get_samples_sex_balsamic(self, case: Case) -> dict[str, dict[str, str]]:
        """Return sex information from StatusDB and from analysis prediction (UNKNOWN for BALSAMIC)."""
        samples_sex: dict[str, dict[str, str]] = {}
        for case_sample in case.links:
            if case_sample.sample.is_tumour:
                continue
            sample_id: str = case_sample.sample.internal_id
            samples_sex[sample_id] = {
                "pedigree": case_sample.sample.sex,
                "analysis": Sex.UNKNOWN,
            }
        return samples_sex

    def get_samples_sex_mip_dna(self, case: Case, hk_version: Version) -> dict[str, dict[str, str]]:
        """Return sex information from StatusDB and from analysis prediction (stored Housekeeper QC metrics file)."""
        qc_metrics_file: Path = self.get_qcmetrics_file(case_id=case.internal_id)
        analysis_sexes: dict = self.get_analysis_sex_mip_dna(self, qc_metrics_file)
        samples_sex: dict[str, dict[str, str]] = {}
        for case_sample in case.links:
            sample_id: str = case_sample.sample.internal_id
            samples_sex[sample_id] = {
                "pedigree": case_sample.sample.sex,
                "analysis": analysis_sexes[sample_id],
            }
        return samples_sex

    def get_analysis_sex_mip_dna(self, qc_metrics_file: Path) -> dict:
        """Return analysis sex for each sample of an analysis."""
        LOG.info("qc_metrics stuff")
        qc_metrics = self.get_parsed_qc_metrics_data_mip_dna(qc_metrics_file)
        return {
            sample_id_metric.sample_id: sample_id_metric.predicted_sex
            for sample_id_metric in qc_metrics.sample_id_metrics
        }

    def get_parsed_qc_metrics_data_mip_dna(self, qc_metrics_file: Path) -> MIPMetricsDeliverables:
        """Parse and return a QC metrics file."""
        qcmetrics_raw: dict = ReadFile.get_content_from_file(
            file_format=FileFormat.YAML, file_path=qc_metrics_file
        )
        return MIPMetricsDeliverables(**qcmetrics_raw)

    def get_samples_sex_raredisease(
        self, case: Case, hk_version: Version
    ) -> dict[str, dict[str, str]]:
        """Return sex information from StatusDB and from analysis prediction (stored Housekeeper QC metrics file)."""
        qc_metrics_file: Path = self.get_qcmetrics_file(case_id=case.internal_id)
        samples_sex: dict[str, dict[str, str]] = {}
        for case_sample in case.links:
            sample_id: str = case_sample.sample.internal_id
            samples_sex[sample_id] = {
                "pedigree": case_sample.sample.sex,
                "analysis": self.get_analysis_sex_raredisease(
                    qc_metrics_file=qc_metrics_file, sample_id=sample_id
                ),
            }
        return samples_sex

    def get_analysis_sex_raredisease(self, qc_metrics_file: Path, sample_id: str) -> str:
        """Return analysis sex for each sample of an analysis."""
        qc_metrics: list[MetricsBase] = self.get_parsed_qc_metrics_data_raredisease(qc_metrics_file)
        for metric in qc_metrics:
            if metric.name == RAREDISEASE_PREDICTED_SEX_METRIC and metric.id == sample_id:
                return str(metric.value)

    def get_parsed_qc_metrics_data_raredisease(self, qc_metrics: Path) -> list[MetricsBase]:
        """Parse and return a QC metrics file."""
        qcmetrics_raw: dict = ReadFile.get_content_from_file(
            file_format=FileFormat.YAML, file_path=qc_metrics
        )
        return [MetricsBase(**metric) for metric in qcmetrics_raw["metrics"]]

    def get_qcmetrics_file(self, case_id:str) -> Path:
        """Return a QC metrics file path."""
        tags: set[str] = {HkAnalysisMetricsTag.QC_METRICS}
        hk_qcmetrics: File = self.hk.get_file_from_latest_version(bundle_name=case_id, tags=tags)
        if not hk_qcmetrics:
            raise FileNotFoundError("QC metrics file not found for the given Housekeeper version.")
        LOG.debug(f"Found QC metrics file {hk_qcmetrics.full_path}")
        return Path(hk_qcmetrics.full_path)

        tags: set[str] = {GenotypeAnalysisTag.GENOTYPE}
        return self.hk.get_file_from_latest_version(bundle_name=case_id, tags=tags)

