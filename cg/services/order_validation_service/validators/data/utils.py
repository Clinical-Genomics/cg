from cg.store.models import Application
from cg.store.store import Store


def is_application_archived(application_tag: str, store: Store):
    application: Application | None = store.get_application_by_tag(application_tag)
    return application and application.is_archived
