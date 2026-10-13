from cg.services.analysis_starter.input_fetcher.input_fetcher import InputFetcher


class SkipFetcher(InputFetcher):
    """To be used when no archiving is in place for a workflow, e.g. for the Trana workflow."""

    def ensure_files_are_ready(self, case_id: str):
        pass
