import os
from os.path import isfile
from pathlib import Path

from cg.models.cg_config import RarediseaseConfig
from cg.services.analysis_starter.configurator.extensions.pipeline_extension import (
    PipelineExtension,
)
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from cg.services.analysis_starter.configurator.file_creators.managed_variants import (
    ManagedVariantsFileCreator,
)

GENE_PANEL_FILE_NAME = "gene_panels.bed"
MANAGED_VARIANTS_FILE_NAME = "managed_variants.vcf"


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
        self.config = raredisease_config

    def configure(self, case_id: str, case_run_directory: Path) -> None:
        """Perform pipeline specific actions."""
        self.gene_panel_file_creator.create(
            case_id=case_id, file_path=_get_gene_panel_file_path(case_run_directory)
        )
        self.managed_variants_file_creator.create(
            case_id=case_id, file_path=_get_managed_variants(case_run_directory)
        )
        self._copy_rank_model_files(case_run_directory)

    def do_required_files_exist(self, case_run_directory: Path) -> bool:
        # TODO: Add existence checks for case directory rank model files
        return isfile(_get_gene_panel_file_path(case_run_directory)) and isfile(
            _get_managed_variants(case_run_directory)
        )

    def _copy_rank_model_files(self, case_run_directory: Path) -> None:
        """Copy rank model files to the case run directory."""
        snv_rank_model_file = Path(self.config.rank_model_snv)
        sv_rank_model = Path(self.config.rank_model_sv)
        os.link(snv_rank_model_file, case_run_directory / snv_rank_model_file.name)
        os.link(sv_rank_model, case_run_directory / sv_rank_model.name)


def _get_gene_panel_file_path(case_run_directory: Path) -> Path:
    return case_run_directory.joinpath(GENE_PANEL_FILE_NAME)


def _get_managed_variants(case_run_directory: Path):
    return case_run_directory.joinpath(MANAGED_VARIANTS_FILE_NAME)
