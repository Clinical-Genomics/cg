import logging
from subprocess import CalledProcessError

from cg.services.analysis_starter.configurator.abstract_model import CaseConfig
from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.input_fetcher.input_fetcher import InputFetcher
from cg.services.analysis_starter.submitters.submitter import Submitter
from cg.services.analysis_starter.tracker.tracker import Tracker

LOG = logging.getLogger(__name__)


class AnalysisStarter:
    def __init__(
        self,
        configurator: Configurator,
        input_fetcher: InputFetcher,
        submitter: Submitter,
        tracker: Tracker,
    ):
        self.configurator = configurator
        self.input_fetcher = input_fetcher
        self.submitter = submitter
        self.tracker = tracker

    def start(self, case_id: str, **flags):
        """Fetches raw data, generates configuration files and runs the specified case."""
        self.tracker.ensure_analysis_not_ongoing(case_id)
        self.input_fetcher.ensure_files_are_ready(case_id)
        parameters: CaseConfig = self.configurator.configure(case_id=case_id, **flags)
        self._run_and_track(case_id=case_id, parameters=parameters)

    def run(self, case_id: str, **flags):
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
