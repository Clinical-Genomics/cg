from pathlib import Path

from cg.constants import DEFAULT_CAPTURE_KIT, Pipeline
from cg.constants.constants import AnalysisType
from cg.constants.gene_panel import GENOME_BUILD_37
from cg.constants.pedigree import Pedigree
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import CaseSample
from cg.utils import Process


class MipDNAAnalysisAPI(MipAnalysisAPI):
    def __init__(self, config: CGConfig, pipeline: Pipeline = Pipeline.MIP_DNA):
        super().__init__(config, pipeline)

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
    def mip_pipeline(self) -> str:
        return self.config.mip_rd_dna.pipeline

    @property
    def script(self) -> str:
        return self.config.mip_rd_dna.script

    @property
    def use_read_count_threshold(self) -> bool:
        return True

    @property
    def process(self) -> Process:
        if not self._process:
            self._process = Process(
                binary=f"{self.script} {self.mip_pipeline}",
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

    def get_gene_panel(self, case_id: str) -> list[str]:
        """Create and return the aggregated gene panel file."""
        return self._get_gene_panel(case_id=case_id, genome_build=GENOME_BUILD_37)

    def get_managed_variants(self) -> list[str]:
        """Create and return the managed variants."""
        return self._get_managed_variants(genome_build=GENOME_BUILD_37)
