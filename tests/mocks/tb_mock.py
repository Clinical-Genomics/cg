from cg.apps.tb.models import TrailblazerAnalysis


class MockTB:
    def __init__(self):
        self.analyses_response = []
        self.get_latest_analysis_response = {}

    def is_latest_analysis_ongoing(self, *args, **kwargs) -> bool:
        return False

    def add_pending_analysis(self, *args, **kwargs) -> None:
        return None

    def add_commit(self, *args, **kwargs) -> None:
        return None

    def has_latest_analysis_started(self, *args, **kwargs) -> bool:
        return False

    def analyses(self, *args, **kwargs) -> list:
        return self.analyses_response

    def get_latest_analysis(self, case_id: str) -> TrailblazerAnalysis | None:
        return self.get_latest_analysis_response.get(case_id)

    def get_latest_analysis_status(self, *args, **kwargs) -> None:
        return None

    def ensure_analyses_response(self, analyses_list: list) -> None:
        self.analyses_response = [
            TrailblazerAnalysis.model_validate(analysis) for analysis in analyses_list
        ]

    def ensure_get_latest_analysis_response(self, analysis_dict: dict) -> None:
        self.get_latest_analysis_response[analysis_dict["family"]] = (
            TrailblazerAnalysis.model_validate(analysis_dict)
        )

    def is_latest_analysis_completed(self, case_id: str):
        return True

    def is_latest_analysis_qc(self, case_id: str):
        return True

    def set_analysis_status(self, case_id: str, status: str):
        return

    def add_comment(self, case_id: str, comment: str):
        return

    def get_summaries(self, order_ids: list[int]):
        return []

    def verify_latest_analysis_is_completed(self, case_id: str, force: bool = False):
        return
