from cg.services.delivery_message.messages import DeliveryMessage
from cg.store.models import Case


class ScoutMessage(DeliveryMessage):
    def create_message(self, case: Case):
        pass
