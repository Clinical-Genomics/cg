from datetime import datetime

from cg.store.store import Store


def completed(store: Store):
    def handler(message: dict):
        store.update_analysis_uploaded_at(
            analysis_id=message["cg.analysis_id"],
            uploaded_at=datetime.strptime(message["uploaded_at"], "%Y-%m-%dT%H:%M:%SZ"),
        )

    return handler
