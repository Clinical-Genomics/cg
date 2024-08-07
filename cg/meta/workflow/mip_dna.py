import logging
from pathlib import Path

from cg.constants import DEFAULT_CAPTURE_KIT, Workflow
from cg.constants.constants import AnalysisType, FileFormat
from cg.constants.gene_panel import GENOME_BUILD_37
from cg.constants.pedigree import Pedigree
from cg.io.controller import ReadFile
from cg.constants.scout import MIP_CASE_TAGS
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.mip.mip_analysis import MipAnalysis
from cg.models.mip.mip_metrics_deliverables import MIPMetricsDeliverables
from cg.store.models import Case, CaseSample
from cg.utils import Process
from housekeeper.store.models import Version

LOG = logging.getLogger(__name__)


class MipDNAAnalysisAPI(MipAnalysisAPI):
    def __init__(self, config: CGConfig, workflow: Workflow = Workflow.MIP_DNA):
        super().__init__(config, workflow)

    @property
    def root(self) -> str:
        return self.config.mip_rd_dna.root

    @property
    def conda_binary(self) -> str:
        return self.config.mip_rd_dna.conda_binary

    @property
    def conda_env(self) -> str:
        return self.config.mip_rd_dna.conda_env

    @property
    def mip_workflow(self) -> str:
        return self.config.mip_rd_dna.workflow

    @property
    def script(self) -> str:
        return self.config.mip_rd_dna.script

    @property
    def process(self) -> Process:
        if not self._process:
            self._process = Process(
                binary=f"{self.script} {self.mip_workflow}",
                conda_binary=f"{self.conda_binary}" if self.conda_binary else None,
                config=self.config.mip_rd_dna.mip_config,
                environment=self.conda_env,
            )
        return self._process

    def config_sample(
        self, link_obj: CaseSample, panel_bed: str | None
    ) -> dict[str, str | int | None]:
        """Return config sample data."""
        sample_data: dict[str, str | int] = self.get_sample_data(link_obj=link_obj)
        if sample_data["analysis_type"] == AnalysisType.WHOLE_GENOME_SEQUENCING:
            sample_data["capture_kit"]: str = panel_bed or DEFAULT_CAPTURE_KIT
        else:
            sample_data["capture_kit"]: str | None = panel_bed or self.get_target_bed_from_lims(
                case_id=link_obj.case.internal_id
            )
        if link_obj.mother:
            sample_data[Pedigree.MOTHER.value]: str = link_obj.mother.internal_id
        if link_obj.father:
            sample_data[Pedigree.FATHER.value]: str = link_obj.father.internal_id
        return sample_data

    def get_gene_panel(self, case_id: str, dry_run: bool = False) -> list[str]:
        """Create and return the aggregated gene panel file."""
        return self._get_gene_panel(case_id=case_id, genome_build=GENOME_BUILD_37, dry_run=dry_run)

    def get_managed_variants(self) -> list[str]:
        """Create and return the managed variants."""
        return self._get_managed_variants(genome_build=GENOME_BUILD_37)

    def get_genome_build(self, case_id: str) -> str:
        """Return the reference genome build version of a MIP-DNA analysis."""
        analysis_metadata: MipAnalysis = self.get_latest_metadata(case_id)
        return analysis_metadata.genome_build

    def get_data_analysis_type(self, case_id: str) -> str:
        """
        Return the data analysis type of a MIP-DNA analysis.
        Patch for the typical behaviour of the AnalysisAPI function.
        It does not raise an error with multiple analysis types.
        """
        case: Case = self.get_validated_case(case_id)
        analysis_types: set[str] = {
            link.sample.application_version.application.analysis_type for link in case.links
        }
        if len(analysis_types) > 1:
            LOG.warning(
                f"Multiple analysis types found. Defaulting to {AnalysisType.WHOLE_GENOME_SEQUENCING}."
            )
            return AnalysisType.WHOLE_GENOME_SEQUENCING
        return analysis_types.pop() if analysis_types else None

    def get_samples_sex(self, case: Case, hk_version: Version) -> dict[str, dict[str, str]]:
        """Return sex information from StatusDB and from analysis prediction (stored Housekeeper QC metrics file)."""
        qc_metrics_file: Path = self.get_qcmetrics_file(hk_version)
        analysis_sexes: dict = self._get_analysis_sex(qc_metrics_file)
        samples_sex: dict[str, dict[str, str]] = {}
        for case_sample in case.links:
            sample_id: str = case_sample.sample.internal_id
            samples_sex[sample_id] = {
                "pedigree": case_sample.sample.sex,
                "analysis": analysis_sexes[sample_id],
            }
        return samples_sex

    def _get_analysis_sex(self, qc_metrics_file: Path) -> dict:
        """Return analysis sex for each sample of an analysis."""
        qc_metrics: MIPMetricsDeliverables = self._get_parsed_qc_metrics_data(qc_metrics_file)
        return {
            sample_id_metric.sample_id: sample_id_metric.predicted_sex
            for sample_id_metric in qc_metrics.sample_id_metrics
        }

    @staticmethod
    def _get_parsed_qc_metrics_data(qc_metrics: Path) -> MIPMetricsDeliverables:
        """Parse and return a QC metrics file."""
        qcmetrics_raw: dict = ReadFile.get_content_from_file(
            file_format=FileFormat.YAML, file_path=qc_metrics
        )
        return MIPMetricsDeliverables(**qcmetrics_raw)

    def get_scout_upload_case_tags(self) -> dict:
        """Return MIP DNA Scout upload case tags."""
        return MIP_CASE_TAGS
