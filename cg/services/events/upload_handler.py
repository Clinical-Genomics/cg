from cg.store.store import Store


def completed(store: Store):
    def handler(message: dict):
        # TODO parse date
        store.update_analysis_uploaded_at(
            analysis_id=message["cg.analysis_id"], uploaded_at=message["uploaded_at"]
        )

    return handler
