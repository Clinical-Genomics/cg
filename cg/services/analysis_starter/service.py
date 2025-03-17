from cg.services.analysis_starter.configurator.abstract_model import CaseConfig
from cg.services.analysis_starter.configurator.abstract_service import Configurator
from cg.services.analysis_starter.input_fetcher.input_fetcher import InputFetcher
from cg.services.analysis_starter.submitters.submitter import Submitter


class AnalysisStarter:
    def __init__(
        self, configurator: Configurator, input_fetcher: InputFetcher, submitter: Submitter
    ):
        self.configurator = configurator
        self.input_fetcher = input_fetcher
        self.submitter = submitter

    def start(self, case_id: str):
        """Fetches raw data, generates additional files and runs the specified case."""
        self.input_fetcher.ensure_files_are_ready(case_id)
        case_config: CaseConfig = self.configurator.configure(case_id)
        self.submitter.submit(case_config)

    def run(self, case_id: str):
        """Run a case using an assumed existing configuration."""
        case_config: CaseConfig = self.configurator.get_config(case_id)
        self.submitter.submit(case_config)
