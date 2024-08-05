from cg.constants import Workflow
from cg.constants.gene_panel import GENOME_BUILD_38
from cg.constants.pedigree import Pedigree
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.utils import Process


class MipRNAAnalysisAPI(MipAnalysisAPI):
    def __init__(self, config: CGConfig, workflow: Workflow = Workflow.MIP_RNA):
        super().__init__(config, workflow)

    @property
    def root(self) -> str:
        return self.config.mip_rd_rna.root

    @property
    def conda_binary(self) -> str:
        return self.config.mip_rd_rna.conda_binary

    @property
    def conda_env(self) -> str:
        return self.config.mip_rd_rna.conda_env

    @property
    def mip_workflow(self) -> str:
        return self.config.mip_rd_rna.workflow

    @property
    def script(self) -> str:
        return self.config.mip_rd_rna.script

    @property
    def process(self) -> Process:
        if not self._process:
            self._process = Process(
                binary=f"{self.script} {self.mip_workflow}",
                conda_binary=f"{self.conda_binary}" if self.conda_binary else None,
                config=self.config.mip_rd_rna.mip_config,
                environment=self.conda_env,
            )
        return self._process

    def config_sample(self, link_obj, panel_bed: str | None = None) -> dict[str, str | int]:
        sample_data: dict[str, str | int] = self.get_sample_data(link_obj)
        if link_obj.mother:
            sample_data[Pedigree.MOTHER.value]: str = link_obj.mother.internal_id
        if link_obj.father:
            sample_data[Pedigree.FATHER.value]: str = link_obj.father.internal_id
        return sample_data

    def get_gene_panel(self, case_id: str, dry_run: bool = False) -> list[str]:
        """Create and return the aggregated gene panel file."""
        return self._get_gene_panel(case_id=case_id, genome_build=GENOME_BUILD_38, dry_run=dry_run)

    def get_managed_variants(self) -> list[str]:
        """Create and return the managed variants."""
        return self._get_managed_variants(genome_build=GENOME_BUILD_38)
