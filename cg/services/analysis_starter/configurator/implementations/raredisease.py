import logging

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.constants.nf_analysis import NextflowFileType
from cg.models.cg_config import RarediseaseConfig
from cg.services.analysis_starter.configurator.file_creators.params_file.raredisease import (
    RarediseaseParamsFileContentCreator,
)
from cg.services.analysis_starter.configurator.file_creators.sample_sheet.raredisease import (
    RarediseaseSampleSheetContentCreator,
)
from cg.services.analysis_starter.configurator.file_creators.utils import create_file
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class RarediseaseConfigurator(NextflowConfigurator):
    """Configurator for Raredisease analysis."""

    def __init__(
        self,
        config: RarediseaseConfig,
        store: Store,
        housekeeper_api: HousekeeperAPI,
        lims: LimsAPI,
        sample_sheet_content_creator: RarediseaseSampleSheetContentCreator,
        params_content_creator: RarediseaseParamsFileContentCreator,
    ):
        super().__init__(config=config, store=store, housekeeper_api=housekeeper_api, lims=lims)
        self.sample_sheet_content_creator = sample_sheet_content_creator
        self.params_content_creator = params_content_creator

    def _do_pipeline_specific_actions(self, case_id: str) -> None:
        """Perform pipeline specific actions."""
        self._create_gene_panel(case_id)
        self._create_managed_variants(case_id)

    def _create_gene_panel(self, case_id: str) -> None:
        create_file(
            content_creator=self.gene_panel_content_creator,
            case_path=self._get_case_path(case_id=case_id),
            file_type=NextflowFileType.GENE_PANEL,
        )

    def _create_managed_variants(self, case_id: str) -> None:
        create_file(
            content_creator=self.managed_variants_content_creator,
            case_path=self._get_case_path(case_id=case_id),
            file_type=NextflowFileType.MANAGED_VARIANTS,
        )
