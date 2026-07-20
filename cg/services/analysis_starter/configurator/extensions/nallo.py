import logging
import shutil
from pathlib import Path

from cg.constants.scout import ScoutExportFileName
from cg.models.cg_config import NalloConfig
from cg.services.analysis_starter.configurator.extensions.pipeline_extension import (
    PipelineExtension,
)
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator

LOG = logging.getLogger(__name__)


class NalloExtension(PipelineExtension):
    def __init__(self, gene_panel_file_creator: GenePanelFileCreator, nallo_config: NalloConfig):
        self.gene_panel_file_creator = gene_panel_file_creator
        self.source_snv_rank_model_path = Path(nallo_config.rank_model_snv)
        self.source_sv_rank_model_path = Path(nallo_config.rank_model_sv)

    def configure(self, case_id: str, case_run_directory: Path) -> None:
        self.gene_panel_file_creator.create(
            case_id=case_id,
            file_path=_get_gene_panel_file_path(case_run_directory),
            double_hashtag_filtering=True,
        )
        self._copy_rank_model_files(case_run_directory)

    def do_required_files_exist(self, case_run_directory: Path) -> bool:
        gene_panel_file_path: Path = _get_gene_panel_file_path(case_run_directory)
        case_snv_rank_model_file = Path(case_run_directory, self.source_snv_rank_model_path.name)
        case_sv_rank_model_file = Path(case_run_directory, self.source_sv_rank_model_path.name)
        return all(
            [
                gene_panel_file_path.is_file(),
                case_sv_rank_model_file.is_file(),
                case_snv_rank_model_file.is_file(),
            ]
        )

    def _copy_rank_model_files(self, case_run_directory: Path) -> None:
        """Copy rank model files to the case run directory."""
        shutil.copy2(
            self.source_snv_rank_model_path,
            case_run_directory / self.source_snv_rank_model_path.name,
        )
        LOG.debug(
            f"Copied {self.source_snv_rank_model_path.name} to case directory "
            f"for case {case_run_directory.name}"
        )
        shutil.copy2(
            self.source_sv_rank_model_path, case_run_directory / self.source_sv_rank_model_path.name
        )
        LOG.debug(
            f"Copied {self.source_sv_rank_model_path.name} to case directory "
            f"for case {case_run_directory.name}"
        )


def _get_gene_panel_file_path(case_run_directory: Path) -> Path:
    return case_run_directory.joinpath(ScoutExportFileName.PANELS_TSV)
