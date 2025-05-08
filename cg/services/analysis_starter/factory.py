import logging
from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import Workflow
from cg.constants.nextflow import NEXTFLOW_WORKFLOWS
from cg.meta.archive.archive import SpringArchiveAPI
from cg.meta.compress import CompressAPI
from cg.meta.workflow.fastq import MicrosaltFastqHandler
from cg.models.cg_config import CGConfig, CommonAppConfig
from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.configurator.extensions.abstract import PipelineExtension
from cg.services.analysis_starter.configurator.extensions.raredisease import RarediseaseExtension
from cg.services.analysis_starter.configurator.file_creators.microsalt_config import (
    MicrosaltConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.config_file import (
    NextflowConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.gene_panel import (
    GenePanelFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.managed_variants import (
    ManagedVariantsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.abstract import (
    ParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.raredisease import (
    RarediseaseParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.abstract import (
    NextflowSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.raredisease import (
    RarediseaseSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.implementations.microsalt import (
    MicrosaltConfigurator,
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
from cg.services.analysis_starter.submitters.subprocess.submitter import SubprocessSubmitter
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class AnalysisStarterFactory:
    def __init__(self, cg_config: CGConfig):
        self.cg_config = cg_config
        self.housekeeper_api: HousekeeperAPI = cg_config.housekeeper_api
        self.lims_api: LimsAPI = cg_config.lims_api
        self.store: Store = cg_config.status_db

    def scout_api(self, workflow: Workflow) -> ScoutAPI:
        return (
            self.cg_config.scout_api_38
            if workflow == Workflow.NALLO
            else self.cg_config.scout_api_37
        )

    def get_analysis_starter(self, case_id: str) -> AnalysisStarter:
        workflow: Workflow = self.store.get_case_workflow(case_id)
        LOG.info(f"Getting a {workflow} analysis starter for case {case_id}")
        configurator: Configurator = self._get_configurator(workflow)
        input_fetcher: InputFetcher = self._get_input_fetcher(workflow)
        submitter: Submitter = self._get_submitter(workflow)
        return AnalysisStarter(
            configurator=configurator, input_fetcher=input_fetcher, submitter=submitter
        )

    def _get_configurator(self, workflow: Workflow) -> Configurator:
        if workflow in NEXTFLOW_WORKFLOWS:
            return self._get_nextflow_configurator(workflow)
        elif workflow == Workflow.MICROSALT:
            return self._get_microsalt_configurator()

    def _get_microsalt_configurator(self):
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

    def _get_nextflow_configurator(self, workflow: Workflow) -> NextflowConfigurator:
        config_file_creator = self._get_nextflow_config_file_creator(workflow)
        params_file_creator: ParamsFileCreator = self._get_params_file_creator(workflow)
        sample_sheet_creator: NextflowSampleSheetCreator = self._get_sample_sheet_creator(workflow)
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

    def _get_nextflow_config_file_creator(self, workflow: Workflow) -> NextflowConfigFileCreator:
        pipeline_config: CommonAppConfig = self._get_pipeline_config(workflow)
        return NextflowConfigFileCreator(
            account=pipeline_config.slurm.account,
            platform=pipeline_config.platform,
            resources=pipeline_config.resources,
            store=self.store,
            workflow_config_path=pipeline_config.config,
        )

    def _get_microsalt_config_file_creator(self) -> MicrosaltConfigFileCreator:
        return MicrosaltConfigFileCreator(
            lims_api=self.lims_api,
            queries_path=self.cg_config.microsalt.queries_path,
            store=self.store,
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
            gene_panel_creator: GenePanelFileCreator = self._get_gene_panel_file_creator(workflow)
            managed_variants_creator: ManagedVariantsFileCreator = (
                self._get_managed_variants_file_creator(workflow)
            )
            return RarediseaseExtension(
                gene_panel_file_creator=gene_panel_creator,
                managed_variants_file_creator=managed_variants_creator,
            )

    def _get_gene_panel_file_creator(self, workflow: Workflow) -> GenePanelFileCreator:
        return GenePanelFileCreator(scout_api=self.scout_api(workflow), store=self.store)

    def _get_managed_variants_file_creator(self, workflow: Workflow) -> ManagedVariantsFileCreator:
        return ManagedVariantsFileCreator(scout_api=self.scout_api(workflow), store=self.store)

    def _get_input_fetcher(self, workflow: Workflow) -> InputFetcher:
        if workflow in FASTQ_WORKFLOWS:
            spring_archive_api = SpringArchiveAPI(
                status_db=self.store,
                housekeeper_api=self.housekeeper_api,
                data_flow_config=self.cg_config.data_flow,
            )
            compress_api = CompressAPI(
                hk_api=self.housekeeper_api,
                crunchy_api=self.cg_config.crunchy_api,
                demux_root=self.cg_config.run_instruments.illumina.demultiplexed_runs_dir,
            )
            return FastqFetcher(
                compress_api=compress_api,
                housekeeper_api=self.housekeeper_api,
                spring_archive_api=spring_archive_api,
                status_db=self.store,
            )
        return InputFetcher()

    def _get_submitter(self, workflow: Workflow) -> Submitter:
        if workflow in NEXTFLOW_WORKFLOWS:
            return self._get_seqera_platform_submitter()
        else:
            return SubprocessSubmitter()

    def _get_seqera_platform_submitter(self) -> SeqeraPlatformSubmitter:
        client = SeqeraPlatformClient(config=self.cg_config.seqera_platform)
        return SeqeraPlatformSubmitter(
            client=client,
            compute_environment_ids=self.cg_config.seqera_platform.compute_environments,
        )
