from abc import ABC

from cg.services.analysis_starter.configurator.abstract_model import CaseConfig


class Submitter(ABC):
    def submit(self, case_config: CaseConfig) -> str | None:
        """Submits the case to be run either as a SubProcess or using the Seqera Platform.
        Returns the workflowId if run via the Seqera Platform."""
        pass
