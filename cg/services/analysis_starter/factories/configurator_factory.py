from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import Workflow
from cg.meta.workflow.fastq import MicrosaltFastqHandler, MipFastqHandler
from cg.models.cg_config import CGConfig, CommonAppConfig
from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.configurator.extensions.nallo import NalloExtension
from cg.services.analysis_starter.configurator.extensions.pipeline_extension import (
    PipelineExtension,
)
from cg.services.analysis_starter.configurator.extensions.raredisease import RarediseaseExtension
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from cg.services.analysis_starter.configurator.file_creators.managed_variants import (
    ManagedVariantsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.microsalt_config import (
    MicrosaltConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.mip_dna_config import (
    MIPDNAConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.config_file import (
    NextflowConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.abstract import (
    ParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.nallo import (
    NalloParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.raredisease import (
    RarediseaseParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.rnafusion import (
    RNAFusionParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.taxprofiler import (
    TaxprofilerParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.nallo import (
    NalloSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.protocol import (
    SampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.raredisease import (
    RarediseaseSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.rnafusion import (
    RNAFusionSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.taxprofiler import (
    TaxprofilerSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.implementations.microsalt import (
    MicrosaltConfigurator,
)
from cg.services.analysis_starter.configurator.implementations.mip_dna import MIPDNAConfigurator
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.store.store import Store


class ConfiguratorFactory:

    def __init__(self, cg_config: CGConfig):
        self.cg_config = cg_config
        self.housekeeper_api: HousekeeperAPI = cg_config.housekeeper_api
        self.lims_api: LimsAPI = cg_config.lims_api
        self.store: Store = cg_config.status_db

    def get_configurator(self, workflow: Workflow) -> Configurator:
        match workflow:
            case Workflow.NALLO | Workflow.RAREDISEASE | Workflow.RNAFUSION | Workflow.TAXPROFILER:
                return self._get_nextflow_configurator(workflow)
            case Workflow.MICROSALT:
                return self._get_microsalt_configurator()
            case Workflow.MIP_DNA:
                return self._get_mip_dna_configurator()
            case _:
                raise NotImplementedError

    def _get_nextflow_configurator(self, workflow: Workflow) -> NextflowConfigurator:
        config_file_creator: NextflowConfigFileCreator = self._get_nextflow_config_file_creator(
            workflow
        )
        params_file_creator: ParamsFileCreator = self._get_params_file_creator(workflow)
        sample_sheet_creator: SampleSheetCreator = self._get_sample_sheet_creator(workflow)
        extension: PipelineExtension = self._get_pipeline_extension(workflow)
        return NextflowConfigurator(
            config_file_creator=config_file_creator,
            params_file_creator=params_file_creator,
            pipeline_config=self._get_pipeline_config(workflow),
            sample_sheet_creator=sample_sheet_creator,
            store=self.store,
            pipeline_extension=extension,
        )

    def _get_nextflow_config_file_creator(self, workflow: Workflow) -> NextflowConfigFileCreator:
        pipeline_config: CommonAppConfig = self._get_pipeline_config(workflow)
        return NextflowConfigFileCreator(
            account=pipeline_config.slurm.account,
            platform=pipeline_config.platform,
            resources=pipeline_config.resources,
            store=self.store,
            workflow_config_path=pipeline_config.config,
        )

    def _get_params_file_creator(self, workflow: Workflow) -> ParamsFileCreator:
        params: str = self._get_pipeline_config(workflow).params
        match workflow:
            case Workflow.NALLO:
                return NalloParamsFileCreator(params)
            case Workflow.RAREDISEASE:
                return RarediseaseParamsFileCreator(
                    lims=self.lims_api, store=self.store, params=params
                )
            case Workflow.RNAFUSION:
                return RNAFusionParamsFileCreator(params)
            case Workflow.TAXPROFILER:
                return TaxprofilerParamsFileCreator(params)
            case _:
                raise NotImplementedError(f"There is no params file creator for {workflow}")

    def _get_pipeline_config(self, workflow: Workflow) -> CommonAppConfig:
        return getattr(self.cg_config, workflow)

    def _get_sample_sheet_creator(self, workflow: Workflow) -> SampleSheetCreator:
        match workflow:
            case Workflow.NALLO:
                return NalloSampleSheetCreator(
                    housekeeper_api=self.housekeeper_api, status_db=self.store
                )
            case Workflow.RAREDISEASE:
                return RarediseaseSampleSheetCreator(
                    housekeeper_api=self.cg_config.housekeeper_api,
                    store=self.store,
                )
            case Workflow.RNAFUSION:
                return RNAFusionSampleSheetCreator(
                    housekeeper_api=self.housekeeper_api, store=self.store
                )
            case Workflow.TAXPROFILER:
                return TaxprofilerSampleSheetCreator(
                    housekeeper_api=self.housekeeper_api, store=self.store
                )
            case _:
                raise NotImplementedError(f"No sample sheet creator implemented for {workflow}")

    def _get_pipeline_extension(self, workflow: Workflow) -> PipelineExtension:
        match workflow:
            case Workflow.NALLO:
                gene_panel_creator: GenePanelFileCreator = self._get_gene_panel_file_creator(
                    workflow
                )
                return NalloExtension(gene_panel_file_creator=gene_panel_creator)
            case Workflow.RAREDISEASE:
                gene_panel_creator: GenePanelFileCreator = self._get_gene_panel_file_creator(
                    workflow
                )
                managed_variants_creator: ManagedVariantsFileCreator = (
                    self._get_managed_variants_file_creator(workflow)
                )
                return RarediseaseExtension(
                    gene_panel_file_creator=gene_panel_creator,
                    managed_variants_file_creator=managed_variants_creator,
                )
            case _:
                return PipelineExtension()

    def _get_gene_panel_file_creator(self, workflow: Workflow) -> GenePanelFileCreator:
        return GenePanelFileCreator(scout_api=self._get_scout_api(workflow), store=self.store)

    def _get_managed_variants_file_creator(self, workflow: Workflow) -> ManagedVariantsFileCreator:
        return ManagedVariantsFileCreator(scout_api=self._get_scout_api(workflow), store=self.store)

    def _get_scout_api(self, workflow: Workflow) -> ScoutAPI:
        return (
            self.cg_config.scout_api_38
            if workflow == Workflow.NALLO
            else self.cg_config.scout_api_37
        )

    def _get_microsalt_configurator(self) -> MicrosaltConfigurator:
        return MicrosaltConfigurator(
            config_file_creator=self._get_microsalt_config_file_creator(),
            fastq_handler=MicrosaltFastqHandler(
                housekeeper_api=self.housekeeper_api,
                root_dir=Path(self.cg_config.microsalt.root),
                status_db=self.store,
            ),
            lims_api=self.lims_api,
            microsalt_config=self.cg_config.microsalt,
            store=self.store,
        )

    def _get_microsalt_config_file_creator(self) -> MicrosaltConfigFileCreator:
        return MicrosaltConfigFileCreator(
            lims_api=self.lims_api,
            queries_path=self.cg_config.microsalt.queries_path,
            store=self.store,
        )

    def _get_mip_dna_configurator(self) -> MIPDNAConfigurator:
        root: str = self.cg_config.mip_rd_dna.root
        return MIPDNAConfigurator(
            cg_mip_config=self.cg_config.mip_rd_dna,
            config_file_creator=self._get_mip_dna_config_file_creator(root=root),
            fastq_handler=MipFastqHandler(
                self.housekeeper_api, root_dir=Path(root), status_db=self.store
            ),
            gene_panel_file_creator=self._get_gene_panel_file_creator(Workflow.MIP_DNA),
            managed_variants_file_creator=self._get_managed_variants_file_creator(Workflow.MIP_DNA),
            store=self.store,
        )

    def _get_mip_dna_config_file_creator(self, root: str) -> MIPDNAConfigFileCreator:
        return MIPDNAConfigFileCreator(lims_api=self.lims_api, root=root, store=self.store)
