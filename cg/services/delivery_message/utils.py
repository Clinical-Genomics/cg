from cg.constants.constants import DataDelivery
from cg.services.delivery_message.messages import (
    AnalysisScoutMessage,
    DeliveryMessage,
    FastqMessage,
    FastqScoutMessage,
    ScoutMessage,
)
from cg.store.models import Case


message_map = {
    DataDelivery.FASTQ: FastqMessage,
    DataDelivery.SCOUT: ScoutMessage,
    DataDelivery.FASTQ_SCOUT: FastqScoutMessage,
    DataDelivery.ANALYSIS_SCOUT: AnalysisScoutMessage,
}


def get_message_strategy(case: Case) -> DeliveryMessage:
    message_strategy: FastqMessage = message_map[case.data_analysis]()
    return message_strategy


def get_message(case: Case) -> str:
    message_strategy: DeliveryMessage = get_message_strategy(case)
    return message_strategy.create_message(case)
