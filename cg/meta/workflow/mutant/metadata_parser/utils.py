from cg.constants.constants import ControlOptions
from cg.store.models import Sample


def is_sample_external_negative_control(sample: Sample) -> bool:
    return sample.control == ControlOptions.NEGATIVE

def get_internal_negative_control() -> bool:
    #Query from lims
    return False