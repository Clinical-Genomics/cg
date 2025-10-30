from pathlib import Path

from cg.constants.scout import ScoutExportFileName
from cg.services.analysis_starter.configurator.extensions.abstract import PipelineExtension
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator


class NalloExtension(PipelineExtension):
    def __init__(self, gene_panel_file_creator: GenePanelFileCreator):
        self.gene_panel_file_creator = gene_panel_file_creator

    def configure(self, case_id: str, case_run_directory: Path) -> None:
        self.gene_panel_file_creator.create(
            case_id=case_id, file_path=case_run_directory / ScoutExportFileName.PANELS_TSV
        )
