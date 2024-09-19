from cg.constants.constants import SequencingQCStatus


def qc_bool_to_status(qc_passes: bool) -> SequencingQCStatus:
    return SequencingQCStatus.PASSED if qc_passes else SequencingQCStatus.FAILED
