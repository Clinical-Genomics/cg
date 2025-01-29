import logging
from pathlib import Path

from housekeeper.store.models import File

from cg.apps.gt import GenotypeAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.constants import FileExtensions, FileFormat, Workflow
from cg.constants.housekeeper_tags import GenotypeAnalysisTag, HkAnalysisMetricsTag
from cg.constants.nf_analysis import RAREDISEASE_PREDICTED_SEX_METRIC
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.constants.subject import Sex
from cg.io.controller import ReadFile
from cg.models.deliverables.metric_deliverables import MetricsBase
from cg.models.mip.mip_metrics_deliverables import MIPMetricsDeliverables
from cg.store.models import Analysis, Case, Sample

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

    def get_genotype_data(self, analysis: Analysis) -> dict[dict[str, dict[str, str]]]:
        """Return data about an analysis to load genotypes.

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
        hk_bcf: File = self._get_genotype_file(case_id=case_id)
        genotype_load_config: dict = {"bcf": hk_bcf.full_path}
        if analysis.workflow in [Workflow.BALSAMIC, Workflow.BALSAMIC_UMI]:
            genotype_load_config["samples_sex"] = self._get_samples_sex_balsamic(case=analysis.case)
        elif analysis.workflow == Workflow.MIP_DNA:
            genotype_load_config["samples_sex"] = self._get_samples_sex_mip_dna(case=analysis.case)
        elif analysis.workflow == Workflow.RAREDISEASE:
            genotype_load_config["samples_sex"] = self._get_samples_sex_raredisease(
                case=analysis.case
            )
        else:
            raise ValueError(f"Workflow {analysis.workflow} does not support Genotype upload")
        return genotype_load_config

    def upload(self, genotype_load_config: dict, replace: bool = False):
        """Upload a genotype config for a case."""
        self.gt.upload(
            str(genotype_load_config["bcf"]), genotype_load_config["samples_sex"], force=replace
        )

    @staticmethod
    def is_suitable_for_genotype_upload(case: Case) -> bool:
        """Returns True if there are any non-tumor WHOLE_GENOME_SEQUENCING samples in the case."""
        samples: list[Sample] = case.samples
        return any(
            (
                not sample.is_tumour
                and SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING == sample.prep_category
            )
            for sample in samples
        )

    def _get_genotype_file(self, case_id: str) -> File:
        "Returns latest genotype file in housekeeper for given case, raises FileNotFoundError if not found."
        LOG.debug("Get Genotype files from Housekeeper")
        tags: set[str] = {GenotypeAnalysisTag.GENOTYPE}
        hk_genotype_files: list[File] = self.hk.get_files_from_latest_version(
            bundle_name=case_id, tags=tags
        )
        hk_genotype: File = self._get_single_genotype_file(hk_genotype_files)
        if not hk_genotype:
            raise FileNotFoundError(f"Genotype file not found for {case_id}")
        LOG.debug(f"Found genotype file {hk_genotype.full_path}")
        return hk_genotype

    def _get_samples_sex_balsamic(self, case: Case) -> dict[str, dict[str, str]]:
        """Return sex information from StatusDB and for analysis."""
        samples_sex: dict[str, dict[str, str]] = {}
        for sample in case.samples:
            if sample.is_tumour:
                continue
            sample_id: str = sample.internal_id
            samples_sex[sample_id] = {
                "pedigree": sample.sex,
                "analysis": Sex.UNKNOWN,
            }
        return samples_sex

    def _get_samples_sex_mip_dna(self, case: Case) -> dict[str, dict[str, str]]:
        """Return sex information from StatusDB and from analysis prediction"""
        qc_metrics_file: Path = self._get_qcmetrics_file(case_id=case.internal_id)
        analysis_sex: dict = self._get_analysis_sex_mip_dna(qc_metrics_file)
        samples_sex: dict[str, dict[str, str]] = {}
        for sample in case.samples:
            sample_id: str = sample.internal_id
            samples_sex[sample_id] = {
                "pedigree": sample.sex,
                "analysis": analysis_sex[sample_id],
            }
        return samples_sex

    @staticmethod
    def _get_analysis_sex_mip_dna(qc_metrics_file: Path) -> dict:
        """Return analysis sex for each sample of an analysis."""
        qc_metrics: MIPMetricsDeliverables = (
            UploadGenotypesAPI._get_parsed_qc_metrics_deliverables_mip_dna(qc_metrics_file)
        )
        return {
            sample_id_metric.sample_id: sample_id_metric.predicted_sex
            for sample_id_metric in qc_metrics.sample_id_metrics
        }

    def _get_qcmetrics_file(self, case_id: str) -> Path:
        """Return a QC metrics file path.
        Raises: FileNotFoundError if nothing is found in the Housekeeper bundle."""
        tags: set[str] = HkAnalysisMetricsTag.QC_METRICS
        hk_qcmetrics: File = self.hk.get_file_from_latest_version(bundle_name=case_id, tags=tags)
        if not hk_qcmetrics:
            raise FileNotFoundError("QC metrics file not found for the given Housekeeper version.")
        LOG.debug(f"Found QC metrics file {hk_qcmetrics.full_path}")
        return Path(hk_qcmetrics.full_path)

    @staticmethod
    def _get_parsed_qc_metrics_deliverables_mip_dna(
        qc_metrics_file: Path,
    ) -> MIPMetricsDeliverables:
        """Parse and return a QC metrics file."""
        qcmetrics_raw: dict = ReadFile.get_content_from_file(
            file_format=FileFormat.YAML, file_path=qc_metrics_file
        )
        return MIPMetricsDeliverables(**qcmetrics_raw)

    def _get_samples_sex_raredisease(self, case: Case) -> dict[str, dict[str, str]]:
        """Return sex information from StatusDB and from analysis prediction."""
        qc_metrics_file: Path = self._get_qcmetrics_file(case_id=case.internal_id)
        samples_sex: dict[str, dict[str, str]] = {}
        for sample in case.samples:
            sample_id: str = sample.internal_id
            samples_sex[sample_id] = {
                "pedigree": sample.sex,
                "analysis": self._get_analysis_sex_raredisease(
                    qc_metrics_file=qc_metrics_file, sample_id=sample_id
                ),
            }
        return samples_sex

    def _get_analysis_sex_raredisease(self, qc_metrics_file: Path, sample_id: str) -> str:
        """Return analysis sex for each sample of an analysis."""
        qc_metrics: list[MetricsBase] = self._get_parsed_qc_metrics_deliverables_raredisease(
            qc_metrics_file
        )
        for metric in qc_metrics:
            if metric.name == RAREDISEASE_PREDICTED_SEX_METRIC and metric.id == sample_id:
                return str(metric.value)

    @staticmethod
    def _get_parsed_qc_metrics_deliverables_raredisease(qc_metrics: Path) -> list[MetricsBase]:
        """Parse and return a QC metrics file."""
        qcmetrics_raw: dict = ReadFile.get_content_from_file(
            file_format=FileFormat.YAML, file_path=qc_metrics
        )
        return [MetricsBase(**metric) for metric in qcmetrics_raw["metrics"]]

    @staticmethod
    def _is_variant_file(genotype_file: File):
        return genotype_file.full_path.endswith(
            FileExtensions.VCF_GZ
        ) or genotype_file.full_path.endswith(FileExtensions.BCF)

    def _get_single_genotype_file(self, hk_genotype_files: list[File]) -> File:
        """
        Returns the single .bcf or .vcf.gz file expected to be found in the provided list. Raises an error if the amount of such files is different from 1.
        """
        filtered_files = [file for file in hk_genotype_files if self._is_variant_file(file)]
        if len(filtered_files) != 1:
            raise ValueError(
                f"Error: Expecte one genotype file, but found {len(filtered_files)} "
                f"({', '.join(map(str, filtered_files))})."
            )
        return filtered_files[0]
