import logging
from typing import cast

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Workflow
from cg.meta.archive.archive import SpringArchiveAPI
from cg.meta.compress import CompressAPI
from cg.models.cg_config import CGConfig, CommonAppConfig
from cg.services.analysis_starter.analysis_input_validator.analysis_input_validator import (
    AnalysisInputValidator,
)
from cg.services.analysis_starter.analysis_input_validator.implementations.data_exists_validator import (
    DataExistsValidator,
)
from cg.services.analysis_starter.analysis_input_validator.implementations.fastq_fetcher import (
    FastqFetcher,
)
from cg.services.analysis_starter.analysis_starter import AnalysisStarter
from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.constants import (
    IMPLEMENTED_WORKFLOWS_WITH_COMPRESSION,
    WORKFLOWS_WITHOUT_COMPRESSION,
)
from cg.services.analysis_starter.factories.configurator_factory import ConfiguratorFactory
from cg.services.analysis_starter.submitters.seqera_platform.seqera_platform_client import (
    SeqeraPlatformClient,
)
from cg.services.analysis_starter.submitters.seqera_platform.seqera_platform_submitter import (
    SeqeraPlatformSubmitter,
)
from cg.services.analysis_starter.submitters.submitter import Submitter
from cg.services.analysis_starter.submitters.subprocess.submitter import SubprocessSubmitter
from cg.services.analysis_starter.tracker.implementations.balsamic import BalsamicTracker
from cg.services.analysis_starter.tracker.implementations.microsalt import MicrosaltTracker
from cg.services.analysis_starter.tracker.implementations.mip_dna import MIPDNATracker
from cg.services.analysis_starter.tracker.implementations.nextflow_tracker import NextflowTracker
from cg.services.analysis_starter.tracker.tracker import Tracker
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class AnalysisStarterFactory:
    def __init__(self, cg_config: CGConfig):
        self.cg_config = cg_config
        self.configurator_factory = ConfiguratorFactory(cg_config)
        self.housekeeper_api: HousekeeperAPI = cg_config.housekeeper_api
        self.store: Store = cg_config.status_db

    def get_analysis_starter_for_case(self, case_id: str) -> AnalysisStarter:
        LOG.debug(f"Getting analysis starter for {case_id}")
        workflow: Workflow = self.store.get_case_workflow(case_id)
        return self.get_analysis_starter_for_workflow(workflow)

    def get_analysis_starter_for_workflow(self, workflow: Workflow) -> AnalysisStarter:
        LOG.debug(f"Getting a {workflow} analysis starter")
        configurator: Configurator = self.configurator_factory.get_configurator(workflow)
        input_fetcher: AnalysisInputValidator = self._get_input_validator(workflow)
        submitter: Submitter = self._get_submitter(workflow)
        tracker: Tracker = self._get_tracker(workflow)
        return AnalysisStarter(
            configurator=configurator,
            analysis_input_validator=input_fetcher,
            store=self.store,
            submitter=submitter,
            tracker=tracker,
            workflow=workflow,
        )

    def _get_input_validator(self, workflow: Workflow) -> AnalysisInputValidator:
        if workflow in IMPLEMENTED_WORKFLOWS_WITH_COMPRESSION:
            spring_archive_api = SpringArchiveAPI(
                status_db=self.store,
                housekeeper_api=self.housekeeper_api,
                data_flow_config=self.cg_config.data_flow,
            )
            compress_api = CompressAPI(
                hk_api=self.housekeeper_api,
                crunchy_api=self.cg_config.crunchy_api,
                demux_root=self.cg_config.run_instruments.illumina.demultiplexed_runs_dir,
                status_db=self.store,
            )
            return FastqFetcher(
                compress_api=compress_api,
                housekeeper_api=self.housekeeper_api,
                spring_archive_api=spring_archive_api,
                status_db=self.store,
            )
        elif workflow in WORKFLOWS_WITHOUT_COMPRESSION:
            return DataExistsValidator(status_db=self.store, housekeeper_api=self.housekeeper_api)
        raise NotImplementedError(f"No input validator for workflow {workflow}")

    def _get_submitter(self, workflow: Workflow) -> Submitter:
        match workflow:
            case (
                Workflow.NALLO
                | Workflow.RAREDISEASE
                | Workflow.RNAFUSION
                | Workflow.TAXPROFILER
                | Workflow.TOMTE
                | Workflow.TRANA_16S
                | Workflow.TRANA_ITS
            ):
                return self._get_seqera_platform_submitter()
            case (
                Workflow.BALSAMIC
                | Workflow.BALSAMIC_PON
                | Workflow.BALSAMIC_UMI
                | Workflow.FLUFFY
                | Workflow.MICROSALT
                | Workflow.MIP_DNA
                | Workflow.MIP_RNA
                | Workflow.MUTANT
            ):
                return SubprocessSubmitter()
            case _:
                raise NotImplementedError(f"No submitter configured for workflow {workflow}")

    def _get_seqera_platform_submitter(self) -> SeqeraPlatformSubmitter:
        client = SeqeraPlatformClient(config=self.cg_config.seqera_platform)
        return SeqeraPlatformSubmitter(
            client=client,
            compute_environment_ids=self.cg_config.seqera_platform.compute_environments,
        )

    def _get_tracker(self, workflow: Workflow) -> Tracker:
        match workflow:
            case (
                Workflow.NALLO
                | Workflow.RAREDISEASE
                | Workflow.RNAFUSION
                | Workflow.TAXPROFILER
                | Workflow.TOMTE
                | Workflow.TRANA_16S
                | Workflow.TRANA_ITS
            ):
                return NextflowTracker(
                    store=self.store,
                    trailblazer_api=self.cg_config.trailblazer_api,
                    workflow_root=cast(
                        CommonAppConfig, self.cg_config.get_pipeline_config(workflow)
                    ).root,
                )
            case Workflow.MICROSALT:
                return MicrosaltTracker(
                    store=self.store,
                    subprocess_submitter=SubprocessSubmitter(),
                    trailblazer_api=self.cg_config.trailblazer_api,
                    workflow_root=self.cg_config.microsalt.root,
                )
            case Workflow.BALSAMIC | Workflow.BALSAMIC_UMI:
                return BalsamicTracker(
                    store=self.store,
                    trailblazer_api=self.cg_config.trailblazer_api,
                    workflow_root=str(self.cg_config.balsamic.root),
                )
            case Workflow.MIP_DNA:
                return MIPDNATracker(
                    store=self.store,
                    trailblazer_api=self.cg_config.trailblazer_api,
                    workflow_root=self.cg_config.mip_rd_dna.root,
                )
            case _:
                raise NotImplementedError(f"No {workflow} tracker")
