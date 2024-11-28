from cg.constants.constants import DataDelivery, MicrosaltAppTags, Workflow
from cg.exc import (
    CaseNotFoundError,
    DeliveryMessageNotSupportedError,
    OrderMismatchError,
)
from cg.services.delivery_message.messages import (
    AnalysisScoutMessage,
    CovidMessage,
    FastqAnalysisScoutMessage,
    FastqMessage,
    FastqScoutMessage,
    MicrosaltMwrMessage,
    ScoutMessage,
    StatinaMessage,
)
from cg.services.delivery_message.messages.analysis_message import AnalysisMessage
from cg.services.delivery_message.messages.bam_message import BamMessage
from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.fastq_analysis_message import (
    FastqAnalysisMessage,
)
from cg.services.delivery_message.messages.microsalt_mwx_message import (
    MicrosaltMwxMessage,
)
from cg.store.models import Case, Sample


def get_message(cases: list[Case]) -> str:
    message_strategy: DeliveryMessage = get_message_strategy(cases[0])
    return message_strategy.create_message(cases)


def get_message_strategy(case: Case) -> DeliveryMessage:
    if case.data_analysis == Workflow.MICROSALT:
        return get_microsalt_message_strategy(case)

    if case.data_analysis == Workflow.MUTANT:
        return CovidMessage()

    message_strategy: DeliveryMessage = get_message_strategy_from_data_delivery(case)
    return message_strategy


def get_message_strategy_from_data_delivery(case: Case) -> DeliveryMessage:
    message_strategy: DeliveryMessage = message_map[case.data_delivery]()
    return message_strategy


message_map = {
    DataDelivery.ANALYSIS_FILES: AnalysisMessage,
    DataDelivery.FASTQ: FastqMessage,
    DataDelivery.SCOUT: ScoutMessage,
    DataDelivery.FASTQ_SCOUT: FastqScoutMessage,
    DataDelivery.FASTQ_ANALYSIS: FastqAnalysisMessage,
    DataDelivery.ANALYSIS_SCOUT: AnalysisScoutMessage,
    DataDelivery.FASTQ_ANALYSIS_SCOUT: FastqAnalysisScoutMessage,
    DataDelivery.STATINA: StatinaMessage,
    DataDelivery.BAM: BamMessage,
}


def get_microsalt_message_strategy(case: Case) -> DeliveryMessage:
    if has_mwx_samples(case) or has_vwg_samples(case):
        return MicrosaltMwxMessage()

    if has_mwr_samples(case):
        return MicrosaltMwrMessage()

    app_tag: str = get_case_app_tag(case)
    raise NotImplementedError(f"Microsalt apptag {app_tag} not supported.")


def has_mwx_samples(case: Case):
    case_app_tag: str = get_case_app_tag(case)
    return case_app_tag == MicrosaltAppTags.MWXNXTR003


def has_mwr_samples(case: Case):
    case_app_tag: str = get_case_app_tag(case)
    return case_app_tag == MicrosaltAppTags.MWRNXTR003


def has_vwg_samples(case: Case):
    case_app_tag: str = get_case_app_tag(case)
    return case_app_tag == MicrosaltAppTags.VWGNXTR001


def get_case_app_tag(case: Case) -> str:
    sample: Sample = case.samples[0]
    return get_sample_app_tag(sample)


def get_sample_app_tag(sample: Sample) -> str:
    return sample.application_version.application.tag


def validate_cases(cases: list[Case], case_ids: list[str]) -> None:
    if set(case_ids) != set(case.internal_id for case in cases):
        raise CaseNotFoundError("Internal id not found in the database")
    if not is_matching_order(cases):
        raise OrderMismatchError("Cases do not belong to the same order")
    cases_with_mip_rna: list[Case] = [
        case for case in cases if case.data_analysis == Workflow.MIP_RNA
    ]
    if cases_with_mip_rna:
        raise DeliveryMessageNotSupportedError("Workflow is not supported.")


def is_matching_order(cases: list[Case]) -> bool:
    return all([case.latest_order == cases[0].latest_order for case in cases])
