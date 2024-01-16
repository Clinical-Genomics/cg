from cg.services.delivery_message.messages import DeliveryMessage
from cg.store.models import Case


class ScoutMessage(DeliveryMessage):
    def create_message():
        return f"Hello,\n\n The following case has been uploaded to Scout:\n\n links"
