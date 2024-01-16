from cg.constants.constants import DataDelivery, MicrosaltAppTags, Pipeline
from cg.services.delivery_message.messages import (
    AnalysisScoutMessage,
    CovidMessage,
    DeliveryMessage,
    FastqMessage,
    FastqScoutMessage,
    FastqAnalysisScoutMessage,
    MicrosaltMwrMessage,
    MicrosaltMwxMessage,
    ScoutMessage,
)
from cg.services.delivery_message.messages.microsalt_mwx_message import MicrosaltMwxMessage
from cg.store.models import Case, Sample


message_map = {
    DataDelivery.FASTQ: FastqMessage,
    DataDelivery.SCOUT: ScoutMessage,
    DataDelivery.FASTQ_SCOUT: FastqScoutMessage,
    DataDelivery.ANALYSIS_SCOUT: AnalysisScoutMessage,
    DataDelivery.FASTQ_ANALYSIS_SCOUT: FastqAnalysisScoutMessage,
}


def get_message_strategy(case: Case) -> DeliveryMessage:
    if case.data_analysis == Pipeline.MICROSALT:
        return get_microsalt_message_strategy(case)

    if case.data_analysis == Pipeline.SARS_COV_2:
        return CovidMessage()

    message_strategy: DeliveryMessage = message_map[case.data_analysis]()
    return message_strategy


def get_microsalt_message_strategy(case: Case) -> DeliveryMessage:
    if has_mwx_samples(case):
        return MicrosaltMwxMessage()

    if has_mwr_samples(case):
        return MicrosaltMwrMessage()

    app_tag: str = get_case_app_tag(case)
    raise NotImplementedError(f"Microsalt apptag {app_tag} not supported.")


def get_message(case: Case) -> str:
    message_strategy: DeliveryMessage = get_message_strategy(case)
    return message_strategy.create_message(case)


def has_mwx_samples(case: Case):
    case_app_tag: str = get_case_app_tag(case)
    return case_app_tag == MicrosaltAppTags.MWXNXTR003


def has_mwr_samples(case: Case):
    case_app_tag: str = get_case_app_tag(case)
    return case_app_tag == MicrosaltAppTags.MWRNXTR003


def get_case_app_tag(case: Case) -> str:
    sample: Sample = case.samples[0]
    return get_sample_app_tag(sample)


def get_sample_app_tag(sample: Sample) -> str:
    return sample.application_version.application.tag
