from cg.constants.constants import DataDelivery, MicrosaltAppTags, Workflow
from cg.exc import CaseNotFoundError, OrderMismatchError
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
from cg.services.delivery_message.messages.fastq_analysis_message import FastqAnalysisMessage
from cg.services.delivery_message.messages.microsalt_mwx_message import MicrosaltMwxMessage
from cg.services.delivery_message.messages.rna_delivery_message import (
    RNAScoutStrategy,
    RNAFastqStrategy,
    RNAAnalysisStrategy,
    RNAFastqAnalysisStrategy,
    RNAUploadMessageStrategy,
    RNADeliveryMessage,
)
from cg.store.models import Case, Sample
from cg.store.store import Store

MESSAGE_MAP = {
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


RNA_STRATEGY_MAP: dict[DataDelivery, type[RNAUploadMessageStrategy]] = {
    # Only returns a message strategy if there is a scout delivery for the case.
    DataDelivery.SCOUT: RNAScoutStrategy,
    DataDelivery.FASTQ_SCOUT: RNAFastqStrategy,
    DataDelivery.ANALYSIS_SCOUT: RNAAnalysisStrategy,
    DataDelivery.FASTQ_ANALYSIS_SCOUT: RNAFastqAnalysisStrategy,
}


def get_message(cases: list[Case], store: Store) -> str:
    message_strategy: DeliveryMessage = get_message_strategy(cases[0], store)
    return message_strategy.create_message(cases)


def get_message_strategy(case: Case, store: Store) -> DeliveryMessage:
    if case.data_analysis == Workflow.MICROSALT:
        return get_microsalt_message_strategy(case)

    if case.data_analysis == Workflow.MUTANT:
        return CovidMessage()

    if case.data_analysis == Workflow.MIP_RNA:
        return get_rna_message_strategy_from_data_delivery(case=case, store=store)

    message_strategy: DeliveryMessage = get_message_strategy_from_data_delivery(case)
    return message_strategy


def get_message_strategy_from_data_delivery(case: Case) -> DeliveryMessage:
    message_strategy: DeliveryMessage = MESSAGE_MAP[case.data_delivery]()
    return message_strategy


def get_rna_message_strategy_from_data_delivery(
    case: Case, store: Store
) -> DeliveryMessage | RNADeliveryMessage:
    """Get the RNA delivery message strategy based on the data delivery type.
    If a scout delivery is required it will use the RNADeliveryMessage class that links RNA to DNA cases.
    Otherwise it used the conventional delivery message strategy.
    """
    message_strategy = RNA_STRATEGY_MAP[case.data_delivery]
    if message_strategy:
        return RNADeliveryMessage(store=store, strategy=message_strategy())
    return MESSAGE_MAP[case.data_delivery]()


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


def is_matching_order(cases: list[Case]) -> bool:
    return all([case.latest_order == cases[0].latest_order for case in cases])
