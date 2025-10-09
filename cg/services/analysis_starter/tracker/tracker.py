import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from cg.apps.environ import environ_email
from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants.constants import CaseActions, CustomerId, Workflow
from cg.constants.priority import TrailblazerPriority
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.constants.tb import AnalysisType
from cg.exc import AnalysisRunningError
from cg.meta.workflow.utils.utils import MAP_TO_TRAILBLAZER_PRIORITY
from cg.services.analysis_starter.configurator.abstract_model import CaseConfig
from cg.store.models import Analysis, Case, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class Tracker(ABC):
    """Ensures tracking of started analyses. This mainly means exporting analyses to Trailblazer."""

    def __init__(
        self,
        store: Store,
        trailblazer_api: TrailblazerAPI,
        workflow_root: str,
    ):
        self.store = store
        self.trailblazer_api = trailblazer_api
        self.workflow_root = workflow_root

    def track(
        self,
        case_config: CaseConfig,
        tower_workflow_id: str | None = None,
    ) -> None:
        tb_analysis: TrailblazerAnalysis = self._track_in_trailblazer(
            case_id=case_config.case_id, tower_workflow_id=tower_workflow_id
        )
        LOG.info(
            f"Analysis entry for case {case_config.case_id} created in Trailblazer with id {tb_analysis.id}"
        )
        self._create_analysis_statusdb(case_config=case_config, trailblazer_id=tb_analysis.id)
        LOG.info(f"Analysis entry for case {case_config.case_id} created in StatusDB")

    def ensure_analysis_not_ongoing(self, case_id: str) -> None:
        """Raises: AnalysisRunningError if the case has an analysis running in Trailblazer."""
        if self.trailblazer_api.is_latest_analysis_ongoing(case_id):
            raise AnalysisRunningError(f"Analysis still ongoing in Trailblazer for case {case_id}")
        LOG.info(f"No ongoing analysis in Trailblazer for case {case_id}")

    def set_case_as_running(self, case_id: str) -> None:
        self.store.update_case_action(case_internal_id=case_id, action=CaseActions.RUNNING)

    def set_case_as_not_running(self, case_id: str) -> None:
        self.store.update_case_action(case_internal_id=case_id, action=None)

    def _track_in_trailblazer(
        self, case_id: str, tower_workflow_id: int | None
    ) -> TrailblazerAnalysis:
        analysis_type: str = self._get_analysis_type(case_id)
        config_path: Path = self._get_job_ids_path(case_id)
        email: str = environ_email()
        order_id: int = self.store.get_case_by_internal_id(case_id).latest_order.id
        out_dir: str = config_path.parent.as_posix()
        priority: TrailblazerPriority = self._get_trailblazer_priority(case_id)
        ticket: str = self.store.get_latest_ticket_from_case(case_id)
        is_case_for_development: bool = self._is_case_for_development(case_id)
        return self.trailblazer_api.add_pending_analysis(
            analysis_type=analysis_type,
            case_id=case_id,
            config_path=config_path.as_posix(),
            email=email,
            order_id=order_id,
            out_dir=out_dir,
            priority=priority,
            ticket=ticket,
            workflow=self.store.get_case_workflow(case_id),
            workflow_manager=self._workflow_manager(),
            tower_workflow_id=tower_workflow_id,
            is_hidden=is_case_for_development,
        )

    def _create_analysis_statusdb(
        self, case_config: CaseConfig, trailblazer_id: int | None
    ) -> None:
        """Storing an analysis bundle in StatusDB for a provided case."""
        case_id: str = case_config.case_id
        LOG.info(f"Storing analysis in StatusDB for {case_id}")
        case: Case = self.store.get_case_by_internal_id(case_id)
        is_primary: bool = len(case.analyses) == 0
        analysis_start: datetime = datetime.now()
        workflow_version: str = self._get_workflow_version(case_config)
        new_analysis: Analysis = self.store.add_analysis(
            workflow=Workflow(case.data_analysis),
            version=workflow_version,
            completed_at=None,
            primary=is_primary,
            started_at=analysis_start,
            trailblazer_id=trailblazer_id,
        )
        new_analysis.case = case
        self.store.add_item_to_store(new_analysis)
        self.store.commit_to_store()
        LOG.info(f"Analysis successfully stored in StatusDB: {case_id} : {analysis_start}")

    def _get_analysis_type(self, case_id: str) -> str:
        """
        Return the analysis type for sample.
        Only analysis types supported by Trailblazer are valid outputs.
        """
        sample: Sample = self.store.get_case_by_internal_id(case_id).samples[0]
        prep_category: str = sample.prep_category
        if prep_category and prep_category.lower() in {
            SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
            SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
            SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
            SeqLibraryPrepCategory.WHOLE_TRANSCRIPTOME_SEQUENCING,
        }:
            return prep_category.lower()
        return AnalysisType.OTHER

    def _get_trailblazer_priority(self, case_id: str) -> TrailblazerPriority:
        """Get the priority for the case in Trailblazer."""
        case: Case = self.store.get_case_by_internal_id(internal_id=case_id)
        return MAP_TO_TRAILBLAZER_PRIORITY[case.priority]

    def _is_case_for_development(self, case_id: str) -> bool:
        case: Case = self.store.get_case_by_internal_id(case_id)
        return case.customer.internal_id == CustomerId.CG_INTERNAL_CUSTOMER

    @abstractmethod
    def _workflow_manager(self):
        pass

    @abstractmethod
    def _get_job_ids_path(self, case_id: str):
        pass

    @abstractmethod
    def _get_workflow_version(self, case_config: CaseConfig) -> str:
        pass
