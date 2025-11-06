from pathlib import Path

from cg.constants.scout import ScoutExportFileName
from cg.services.analysis_starter.configurator.extensions.pipeline_extension import (
    PipelineExtension,
)
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator


class NalloExtension(PipelineExtension):
    def __init__(self, gene_panel_file_creator: GenePanelFileCreator):
        self.gene_panel_file_creator = gene_panel_file_creator

    def configure(self, case_id: str, case_run_directory: Path) -> None:
        self.gene_panel_file_creator.create(
            case_id=case_id,
            file_path=self._get_gene_panel_file_path(case_run_directory),
            double_hashtag_filtering=True,
        )

    def do_required_files_exist(self, case_run_directory: Path) -> bool:
        gene_panel_file_path: Path = self._get_gene_panel_file_path(case_run_directory)
        return gene_panel_file_path.is_file()

    @staticmethod
    def _get_gene_panel_file_path(case_run_directory: Path) -> Path:
        return case_run_directory.joinpath(ScoutExportFileName.PANELS_TSV)
