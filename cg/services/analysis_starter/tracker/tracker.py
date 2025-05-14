from abc import ABC, abstractmethod
from pathlib import Path

from cg.apps.environ import environ_email
from cg.apps.tb import TrailblazerAPI
from cg.constants.constants import CustomerId
from cg.constants.priority import TrailblazerPriority
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.constants.tb import AnalysisType
from cg.exc import CgError
from cg.meta.workflow.utils.utils import MAP_TO_TRAILBLAZER_PRIORITY
from cg.models.cg_config import CommonAppConfig
from cg.store.models import Case, Sample
from cg.store.store import Store


class Tracker(ABC):
    """Ensures tracking of started analyses. This mainly means exporting analyses to Trailblazer."""

    def __init__(
        self, store: Store, trailblazer_api: TrailblazerAPI, workflow_config: CommonAppConfig
    ):
        self.store = store
        self.trailblazer_api = trailblazer_api
        self.workflow_config = workflow_config

    def track(
        self,
        case_id: str,
        tower_workflow_id: str | None = None,
    ) -> None:
        if self.trailblazer_api.is_latest_analysis_ongoing(case_id):
            raise CgError(f"Analysis still ongoing in Trailblazer for case {case_id}")
        analysis_type: str = self._get_analysis_type(case_id)
        config_path: Path = self._get_job_ids_path(case_id)
        email: str = environ_email()
        order_id: int = self.store.get_case_by_internal_id(case_id).latest_order.id
        out_dir: str = config_path.parent.as_posix()
        priority: TrailblazerPriority = self._get_trailblazer_priority(case_id)
        ticket: str = self.store.get_latest_ticket_from_case(case_id)
        is_case_for_development: bool = self._is_case_for_development(case_id)
        self.trailblazer_api.add_pending_analysis(
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

    def _get_analysis_type(self, case_id: str) -> str:
        """
        Return the analysis type for sample.
        Only analysis types supported by Trailblazer
        are valid outputs.
        """
        sample: Sample = self.store.get_case_by_internal_id(case_id).links[0].sample
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
    def _get_job_ids_path(self, case_id):
        pass
