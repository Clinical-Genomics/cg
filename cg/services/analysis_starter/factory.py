from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import Workflow
from cg.constants.nextflow import NEXTFLOW_WORKFLOWS
from cg.meta.archive.archive import SpringArchiveAPI
from cg.models.cg_config import CGConfig, CommonAppConfig
from cg.services.analysis_starter.configurator.abstract_service import Configurator
from cg.services.analysis_starter.configurator.extensions.abstract import PipelineExtension
from cg.services.analysis_starter.configurator.extensions.raredisease import RarediseaseExtension
from cg.services.analysis_starter.configurator.file_creators.config_file import (
    NextflowConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from cg.services.analysis_starter.configurator.file_creators.managed_variants import (
    ManagedVariantsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.params_file.abstract import (
    ParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.params_file.raredisease import (
    RarediseaseParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.sample_sheet.abstract import (
    NextflowSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.sample_sheet.raredisease import (
    RarediseaseSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.constants import FASTQ_WORKFLOWS
from cg.services.analysis_starter.input_fetcher.implementations.fastq_fetcher import FastqFetcher
from cg.services.analysis_starter.input_fetcher.input_fetcher import InputFetcher
from cg.services.analysis_starter.service import AnalysisStarter
from cg.services.analysis_starter.submitters.seqera_platform.client import SeqeraPlatformClient
from cg.services.analysis_starter.submitters.seqera_platform.submitter import (
    SeqeraPlatformSubmitter,
)
from cg.services.analysis_starter.submitters.submitter import Submitter
from cg.store.store import Store


class AnalysisStarterFactory:
    def __init__(self, cg_config: CGConfig):
        self.cg_config = cg_config
        self.housekeeper_api: HousekeeperAPI = cg_config.housekeeper_api
        self.lims_api: LimsAPI = cg_config.lims_api
        self.scout_api: ScoutAPI = cg_config.scout_api
        self.store: Store = cg_config.status_db

    def get_analysis_starter(self, case_id: str) -> AnalysisStarter:
        workflow: Workflow = self.store.get_case_workflow(case_id)
        configurator: Configurator = self._get_configurator(workflow)
        input_fetcher: InputFetcher = self._get_input_fetcher(workflow)
        submitter: Submitter = self._get_submitter(workflow)
        return AnalysisStarter(
            configurator=configurator, input_fetcher=input_fetcher, submitter=submitter
        )

    def _get_configurator(self, workflow: Workflow) -> Configurator:
        if workflow in NEXTFLOW_WORKFLOWS:
            config_file_creator = self._get_config_file_creator(workflow)
            params_file_creator: ParamsFileCreator = self._get_params_file_creator(workflow)
            sample_sheet_creator: NextflowSampleSheetCreator = self._get_sample_sheet_creator(
                workflow
            )
            return NextflowConfigurator(
                config_file_creator=config_file_creator,
                housekeeper_api=self.housekeeper_api,
                lims=self.lims_api,
                params_file_creator=params_file_creator,
                pipeline_config=self._get_pipeline_config(workflow),
                sample_sheet_creator=sample_sheet_creator,
                store=self.store,
                pipeline_extension=self._get_pipeline_extension(workflow),
            )

    def _get_config_file_creator(self, workflow: Workflow) -> NextflowConfigFileCreator:
        pipeline_config: CommonAppConfig = self._get_pipeline_config(workflow)
        return NextflowConfigFileCreator(
            account=pipeline_config.account,
            platform=pipeline_config.platform,
            resources=pipeline_config.resources,
            store=self.store,
            workflow_config_path=pipeline_config.workflow_config_path,
        )

    def _get_params_file_creator(self, workflow: Workflow) -> ParamsFileCreator:
        if workflow == Workflow.RAREDISEASE:
            pipeline_config: CommonAppConfig = self._get_pipeline_config(workflow)
            return RarediseaseParamsFileCreator(
                lims=self.lims_api, store=self.store, params=pipeline_config.params
            )

    def _get_sample_sheet_creator(self, workflow: Workflow) -> NextflowSampleSheetCreator:
        if workflow == Workflow.RAREDISEASE:
            return RarediseaseSampleSheetCreator(
                housekeeper_api=self.cg_config.housekeeper_api,
                lims=self.cg_config.lims_api,
                store=self.store,
            )

    def _get_pipeline_config(self, workflow: Workflow) -> CommonAppConfig:
        return getattr(self.cg_config, workflow)

    def _get_pipeline_extension(self, workflow: Workflow) -> PipelineExtension:
        if workflow == Workflow.RAREDISEASE:
            gene_panel_creator: GenePanelFileCreator = self._get_gene_panel_file_creator()
            managed_variants_creator: ManagedVariantsFileCreator = (
                self._get_managed_variants_file_creator()
            )
            return RarediseaseExtension(
                gene_panel_file_creator=gene_panel_creator,
                managed_variants_file_creator=managed_variants_creator,
            )

    def _get_gene_panel_file_creator(self) -> GenePanelFileCreator:
        return GenePanelFileCreator(scout_api=self.scout_api, store=self.store)

    def _get_managed_variants_file_creator(self) -> ManagedVariantsFileCreator:
        return ManagedVariantsFileCreator(scout_api=self.scout_api, store=self.store)

    def _get_input_fetcher(self, workflow: Workflow) -> InputFetcher:
        if workflow in FASTQ_WORKFLOWS:
            spring_archive_api = SpringArchiveAPI(
                status_db=self.store,
                housekeeper_api=self.housekeeper_api,
                data_flow_config=self.cg_config.data_flow,
            )
            return FastqFetcher(
                compress_api=self.cg_config.meta_apis["compress_api"],
                housekeeper_api=self.housekeeper_api,
                spring_archive_api=spring_archive_api,
                status_db=self.store,
            )
        return InputFetcher()

    def _get_submitter(self, workflow: Workflow) -> Submitter:
        if workflow in NEXTFLOW_WORKFLOWS:
            seqera_platform_client: SeqeraPlatformClient = self._get_seqera_platform_client()
            return SeqeraPlatformSubmitter(
                client=seqera_platform_client,
                compute_environment_ids=self.cg_config.seqera_platform.compute_environments,
            )

    def _get_seqera_platform_client(self) -> SeqeraPlatformClient:
        return SeqeraPlatformClient(self.cg_config.seqera_platform)
