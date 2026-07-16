from pathlib import Path

from cg.constants.scout import ScoutExportFileName
from cg.models.cg_config import NalloConfig
from cg.services.analysis_starter.configurator.extensions.pipeline_extension import (
    PipelineExtension,
)
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from cg.services.analysis_starter.configurator.file_creators.rank_model_file_copier import (
    RankModelFileCopier,
)


class NalloExtension(PipelineExtension):
    def __init__(
        self,
        gene_panel_file_creator: GenePanelFileCreator,
        rank_model_file_copier: RankModelFileCopier,
        nallo_config: NalloConfig,
    ):
        self.gene_panel_file_creator = gene_panel_file_creator
        self.rank_model_file_copier = rank_model_file_copier
        self.nallo_config = nallo_config

    def configure(self, case_id: str, case_run_directory: Path) -> None:
        self.gene_panel_file_creator.create(
            case_id=case_id,
            file_path=self._get_gene_panel_file_path(case_run_directory),
            double_hashtag_filtering=True,
        )
        self.rank_model_file_copier.copy(
            source_snv_file=self.nallo_config.rank_model_snv,
            source_sv_file=self.nallo_config.rank_model_sv,
            destination_directory=case_run_directory,
        )

    def do_required_files_exist(self, case_run_directory: Path) -> bool:
        return all(
            case_run_directory.joinpath(file_name).is_file()
            for file_name in self._get_required_file_names()
        )

    @staticmethod
    def _get_gene_panel_file_path(case_run_directory: Path) -> Path:
        return case_run_directory.joinpath(ScoutExportFileName.PANELS_TSV)

    def _get_required_file_names(self) -> list[str]:
        return [
            ScoutExportFileName.PANELS_TSV,
            self.nallo_config.rank_model_snv.name,
            self.nallo_config.rank_model_sv.name,
        ]
