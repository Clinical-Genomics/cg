from cg.models.orders.constants import OrderType
from cg.services.web_services.application.models import ApplicationResponse
from cg.store.models import Application
from cg.store.store import Store


def create_application_response(app_tags: list[str]) -> ApplicationResponse:
    return ApplicationResponse(applications=app_tags)


class ApplicationsWebService:

    def __init__(self, store: Store):
        self.store = store

    def get_valid_applications(self, order_type: OrderType) -> ApplicationResponse:
        applications: list[Application] = self.store.get_active_applications_by_order_type(
            order_type
        )
        app_tags: list[str] = sorted([application.tag for application in applications])
        return create_application_response(app_tags)

    def update_application_order_types(
        self, application: Application, order_types: list[OrderType]
    ) -> None:
        self.store.delete_order_type_applications_by_application_id(application.id)
        self.store.session.add_all(
            self.store.link_order_types_to_application(
                application=application, order_types=order_types
            )
        )
        self.store.commit_to_store()
