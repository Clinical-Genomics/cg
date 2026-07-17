from pathlib import Path

from cg.models.cg_config import RarediseaseConfig
from cg.services.analysis_starter.configurator.extensions.pipeline_extension import (
    PipelineExtension,
)
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from cg.services.analysis_starter.configurator.file_creators.managed_variants import (
    ManagedVariantsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.rank_model_file_copier import (
    RankModelFileCopier,
)

GENE_PANEL_FILE_NAME = "gene_panels.bed"
MANAGED_VARIANTS_FILE_NAME = "managed_variants.vcf"


class RarediseaseExtension(PipelineExtension):
    """Contains Raredisease specific file creations which differ from the default Nextflow flow."""

    def __init__(
        self,
        gene_panel_file_creator: GenePanelFileCreator,
        managed_variants_file_creator: ManagedVariantsFileCreator,
        rank_model_file_copier: RankModelFileCopier,
        raredisease_config: RarediseaseConfig,
    ):
        self.gene_panel_file_creator = gene_panel_file_creator
        self.managed_variants_file_creator = managed_variants_file_creator
        self.rank_model_file_copier = rank_model_file_copier
        self.raredisease_config = raredisease_config

    def configure(self, case_id: str, case_run_directory: Path) -> None:
        """Perform pipeline specific actions."""
        self.gene_panel_file_creator.create(
            case_id=case_id, file_path=_get_gene_panel_file_path(case_run_directory)
        )
        self.managed_variants_file_creator.create(
            case_id=case_id, file_path=_get_managed_variants(case_run_directory)
        )
        self.rank_model_file_copier.copy(
            source_snv_file=self.raredisease_config.rank_model_snv,
            source_sv_file=self.raredisease_config.rank_model_sv,
            target_directory=case_run_directory,
        )

    def do_required_files_exist(self, case_run_directory: Path) -> bool:
        return all(
            case_run_directory.joinpath(file_name).is_file()
            for file_name in self._get_required_file_names()
        )

    def _get_required_file_names(self) -> list[str]:
        return [
            GENE_PANEL_FILE_NAME,
            MANAGED_VARIANTS_FILE_NAME,
            self.raredisease_config.rank_model_snv.name,
            self.raredisease_config.rank_model_sv.name,
        ]


def _get_gene_panel_file_path(case_run_directory: Path) -> Path:
    return case_run_directory.joinpath(GENE_PANEL_FILE_NAME)


def _get_managed_variants(case_run_directory: Path):
    return case_run_directory.joinpath(MANAGED_VARIANTS_FILE_NAME)
