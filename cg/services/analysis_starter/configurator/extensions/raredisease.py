from pathlib import Path

from cg.constants.scout import ScoutExportFileName
from cg.models.cg_config import RarediseaseConfig
from cg.services.analysis_starter.configurator.extensions.pipeline_extension import (
    PipelineExtension,
)
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from cg.services.analysis_starter.configurator.file_creators.managed_variants import (
    ManagedVariantsFileCreator,
)


class RarediseaseExtension(PipelineExtension):
    """Contains Raredisease specific file creations which differ from the default Nextflow flow."""

    def __init__(
        self,
        gene_panel_file_creator: GenePanelFileCreator,
        managed_variants_file_creator: ManagedVariantsFileCreator,
        raredisease_config: RarediseaseConfig,
    ):
        self.gene_panel_file_creator = gene_panel_file_creator
        self.managed_variants_file_creator = managed_variants_file_creator
        self.source_snv_rank_model_path = Path(raredisease_config.rank_model_snv)
        self.source_sv_rank_model_path = Path(raredisease_config.rank_model_sv)
        self.source_variant_catalog: Path = raredisease_config.variant_catalog

    def configure(self, case_id: str, case_run_directory: Path) -> None:
        """Create or copy to the case directory exclusive files required for running raredisease."""
        self.gene_panel_file_creator.create(
            case_id=case_id, file_path=_get_gene_panel_file_path(case_run_directory)
        )
        self.managed_variants_file_creator.create(
            case_id=case_id, file_path=_get_managed_variants(case_run_directory)
        )
        self._copy_file_to_case_directory(
            source_file_path=self.source_snv_rank_model_path, case_run_directory=case_run_directory
        )
        self._copy_file_to_case_directory(
            source_file_path=self.source_sv_rank_model_path, case_run_directory=case_run_directory
        )
        self._copy_file_to_case_directory(
            source_file_path=self.source_variant_catalog, case_run_directory=case_run_directory
        )

    def do_required_files_exist(self, case_run_directory: Path) -> bool:
        gene_panel_file: Path = _get_gene_panel_file_path(case_run_directory)
        managed_variants_file: Path = _get_managed_variants(case_run_directory)
        case_snv_rank_model_file = Path(case_run_directory, self.source_snv_rank_model_path.name)
        case_sv_rank_model_file = Path(case_run_directory, self.source_sv_rank_model_path.name)
        case_variant_catalog_file = Path(case_run_directory, self.source_variant_catalog.name)
        return all(
            [
                gene_panel_file.is_file(),
                managed_variants_file.is_file(),
                case_snv_rank_model_file.is_file(),
                case_sv_rank_model_file.is_file(),
                case_variant_catalog_file.is_file(),
            ]
        )


def _get_gene_panel_file_path(case_run_directory: Path) -> Path:
    return case_run_directory.joinpath(ScoutExportFileName.PANELS)


def _get_managed_variants(case_run_directory: Path):
    return case_run_directory.joinpath(ScoutExportFileName.MANAGED_VARIANTS)
