from cg.services.application.models import ApplicationResponse
from cg.store.models import Application
from cg.store.store import Store


def create_application_response(app_tags: list[str]) -> ApplicationResponse:
    return ApplicationResponse(applications=app_tags)


class ApplicationsService:

    def __init__(self, store: Store):
        self.store = store

    def get_applications_by_order_type(self, order_type: str) -> ApplicationResponse:
        applications: list[Application] = self.store.get_active_applications_by_order_type(
            order_type
        )
        app_tags: list[str] = [application.tag for application in applications]
        return create_application_response(app_tags)
