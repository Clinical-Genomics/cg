from cg.constants import delivery as constants


def get_delivery_scope(delivery_arguments: set[str]) -> tuple[bool, bool]:
    """Returns the scope of the delivery, ie whether sample and/or case files were delivered."""
    case_delivery: bool = False
    sample_delivery: bool = False
    for delivery in delivery_arguments:
        if (
            constants.PIPELINE_ANALYSIS_TAG_MAP[delivery]["sample_tags"]
            and delivery in constants.ONLY_ONE_CASE_PER_TICKET
        ):
            sample_delivery = True
        if constants.PIPELINE_ANALYSIS_TAG_MAP[delivery]["case_tags"]:
            case_delivery = True
    return sample_delivery, case_delivery
