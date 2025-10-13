import logging
from subprocess import CalledProcessError

from cg.constants import Workflow
from cg.exc import AnalysisNotReadyError
from cg.services.analysis_starter.configurator.abstract_model import CaseConfig
from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.input_fetcher.input_fetcher import InputFetcher
from cg.services.analysis_starter.submitters.submitter import Submitter
from cg.services.analysis_starter.tracker.tracker import Tracker
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class AnalysisStarter:
    def __init__(
        self,
        configurator: Configurator,
        input_fetcher: InputFetcher,
        store: Store,
        submitter: Submitter,
        tracker: Tracker,
        workflow: Workflow,
    ):
        self.configurator = configurator
        self.input_fetcher = input_fetcher
        self.store = store
        self.submitter = submitter
        self.tracker = tracker
        self.workflow = workflow

    def start_available(self, limit: int | None = None) -> bool:
        """Starts available cases. Returns True if all ready cases started without an error."""
        succeeded = True
        cases: list[Case] = self.store.get_cases_to_analyze(workflow=self.workflow, limit=limit)
        LOG.info(f"Found {len(cases)} {self.workflow} cases to start")
        for case in cases:
            try:
                self.start(case.internal_id)
            except AnalysisNotReadyError as error:
                LOG.error(error)
            except Exception as error:
                LOG.error(error)
                succeeded = False
        return succeeded

    def start(self, case_id: str, **flags) -> None:
        """Fetches raw data, generates configuration files and runs the specified case."""
        LOG.info(f"Starting case {case_id}")
        self.tracker.ensure_analysis_not_ongoing(case_id)
        self.input_fetcher.ensure_files_are_ready(case_id)
        parameters: CaseConfig = self.configurator.configure(case_id=case_id, **flags)
        self._run_and_track(case_id=case_id, parameters=parameters)

    def run(self, case_id: str, **flags) -> None:
        """Run a case using an assumed existing configuration."""
        self.tracker.ensure_analysis_not_ongoing(case_id)
        parameters: CaseConfig = self.configurator.get_config(case_id=case_id, **flags)
        self._run_and_track(case_id=case_id, parameters=parameters)

    def _run_and_track(self, case_id: str, parameters: CaseConfig):
        self.tracker.set_case_as_running(case_id)
        try:
            tower_workflow_id: str | None = self.submitter.submit(parameters)
            self.tracker.track(case_config=parameters, tower_workflow_id=tower_workflow_id)
        except CalledProcessError as exception:
            self.tracker.set_case_as_not_running(case_id)
            raise exception
