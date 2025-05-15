from abc import ABC


class Submitter(ABC):
    def submit(self, case_config) -> str | None:
        """Submits the case to be run either as a SubProcess or using the Seqera Platform.
        Returns the workflowId if run via the Seqera Platform."""
        pass
