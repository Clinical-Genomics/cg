import logging

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Workflow
from cg.meta.archive.archive import SpringArchiveAPI
from cg.meta.compress import CompressAPI
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.constants import IMPLEMENTED_FASTQ_WORKFLOWS
from cg.services.analysis_starter.factories.configurator_factory import ConfiguratorFactory
from cg.services.analysis_starter.input_fetcher.implementations.bam_fetcher import BamFetcher
from cg.services.analysis_starter.input_fetcher.implementations.fastq_fetcher import FastqFetcher
from cg.services.analysis_starter.input_fetcher.input_fetcher import InputFetcher
from cg.services.analysis_starter.service import AnalysisStarter
from cg.services.analysis_starter.submitters.seqera_platform.client import SeqeraPlatformClient
from cg.services.analysis_starter.submitters.seqera_platform.submitter import (
    SeqeraPlatformSubmitter,
)
from cg.services.analysis_starter.submitters.submitter import Submitter
from cg.services.analysis_starter.submitters.subprocess.submitter import SubprocessSubmitter
from cg.services.analysis_starter.tracker.implementations.microsalt import MicrosaltTracker
from cg.services.analysis_starter.tracker.implementations.mip_dna import MIPDNATracker
from cg.services.analysis_starter.tracker.implementations.nextflow import NextflowTracker
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
        input_fetcher: InputFetcher = self._get_input_fetcher(workflow)
        submitter: Submitter = self._get_submitter(workflow)
        tracker: Tracker = self._get_tracker(workflow)
        return AnalysisStarter(
            configurator=configurator,
            input_fetcher=input_fetcher,
            store=self.store,
            submitter=submitter,
            tracker=tracker,
            workflow=workflow,
        )

    def _get_input_fetcher(self, workflow: Workflow) -> InputFetcher:
        if workflow in IMPLEMENTED_FASTQ_WORKFLOWS:
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
        elif workflow == Workflow.NALLO:
            return BamFetcher(housekeeper_api=self.housekeeper_api, status_db=self.store)
        raise NotImplementedError(f"No input fetcher for workflow {workflow}")

    def _get_submitter(self, workflow: Workflow) -> Submitter:
        if workflow in [
            Workflow.NALLO,
            Workflow.RAREDISEASE,
            Workflow.RNAFUSION,
            Workflow.TAXPROFILER,
        ]:
            return self._get_seqera_platform_submitter()
        else:
            return SubprocessSubmitter()

    def _get_seqera_platform_submitter(self) -> SeqeraPlatformSubmitter:
        client = SeqeraPlatformClient(config=self.cg_config.seqera_platform)
        return SeqeraPlatformSubmitter(
            client=client,
            compute_environment_ids=self.cg_config.seqera_platform.compute_environments,
        )

    def _get_tracker(self, workflow: Workflow) -> Tracker:
        if workflow in [
            Workflow.NALLO,
            Workflow.RAREDISEASE,
            Workflow.RNAFUSION,
            Workflow.TAXPROFILER,
        ]:
            return NextflowTracker(
                store=self.store,
                trailblazer_api=self.cg_config.trailblazer_api,
                workflow_root=getattr(self.cg_config, workflow).root,
            )
        elif workflow == Workflow.MICROSALT:
            return MicrosaltTracker(
                store=self.store,
                subprocess_submitter=SubprocessSubmitter(),
                trailblazer_api=self.cg_config.trailblazer_api,
                workflow_root=self.cg_config.microsalt.root,
            )
        elif workflow == Workflow.MIP_DNA:
            return MIPDNATracker(
                store=self.store,
                trailblazer_api=self.cg_config.trailblazer_api,
                workflow_root=self.cg_config.mip_rd_dna.root,
            )
