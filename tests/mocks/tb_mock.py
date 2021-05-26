from typing import Optional

from cg.apps.tb.models import TrailblazerAnalysis


class MockTB:
    def __init__(self):
        self.analyses_response = []
        self.get_latest_analysis_response = {}

    def is_latest_analysis_ongoing(self, *args, **kwargs) -> bool:
        return False

    def add_pending_analysis(self, *args, **kwargs) -> None:
        return None

    def mark_analyses_deleted(self, *args, **kwargs) -> None:
        return None

    def add_commit(self, *args, **kwargs) -> None:
        return None

    def has_latest_analysis_started(self, *args, **kwargs) -> bool:
        return False

    def analyses(self, *args, **kwargs) -> list:
        return self.analyses_response

    def get_latest_analysis(self, case_id: str) -> Optional[TrailblazerAnalysis]:
        return self.get_latest_analysis_response.get(case_id)

    def ensure_analyses_response(self, analyses_list: list) -> None:
        self.analyses_response = [
            TrailblazerAnalysis.parse_obj(analysis) for analysis in analyses_list
        ]

    def ensure_get_latest_analysis_response(self, analysis_dict: dict) -> None:
        self.get_latest_analysis_response[analysis_dict["family"]] = TrailblazerAnalysis.parse_obj(
            analysis_dict
        )
