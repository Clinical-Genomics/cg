import os
from pathlib import Path

from cg.constants.scout import ScoutExportFileName
from cg.models.cg_config import NalloConfig
from cg.services.analysis_starter.configurator.extensions.pipeline_extension import (
    PipelineExtension,
)
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator


class NalloExtension(PipelineExtension):
    def __init__(self, gene_panel_file_creator: GenePanelFileCreator, nallo_config: NalloConfig):
        self.gene_panel_file_creator = gene_panel_file_creator
        self.config = nallo_config

    def configure(self, case_id: str, case_run_directory: Path) -> None:
        self.gene_panel_file_creator.create(
            case_id=case_id,
            file_path=self._get_gene_panel_file_path(case_run_directory),
            double_hashtag_filtering=True,
        )
        self._copy_rank_model_files(case_run_directory)

    def do_required_files_exist(self, case_run_directory: Path) -> bool:
        gene_panel_file_path: Path = self._get_gene_panel_file_path(case_run_directory)
        # TODO: Add existence checks for case directory rank model files
        return gene_panel_file_path.is_file()

    def _copy_rank_model_files(self, case_run_directory: Path) -> None:
        """Copy rank model files to the case run directory."""
        snv_rank_model_file = Path(self.config.rank_model_snv)
        sv_rank_model = Path(self.config.rank_model_sv)
        os.link(snv_rank_model_file, case_run_directory / snv_rank_model_file.name)
        os.link(sv_rank_model, case_run_directory / sv_rank_model.name)

    @staticmethod
    def _get_gene_panel_file_path(case_run_directory: Path) -> Path:
        return case_run_directory.joinpath(ScoutExportFileName.PANELS_TSV)
