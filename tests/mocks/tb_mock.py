class MockTB:
    def is_latest_analysis_ongoing(self, *args, **kwargs) -> bool:
        return False

    def add_pending_analysis(self, *args, **kwargs) -> None:
        return None

    def mark_analyses_deleted(self, *args, **kwargs) -> None:
        return None

    def add_commit(self, *args, **kwargs) -> None:
        return None

    def has_latest_analysis_started(self, *args, **kwargs):
        return False

    def analyses(self, *args, **kwargs):
        return []
