from cg.apps.lims.api import LimsAPI
from cg.meta.workflow.mutant.quality_controller.utils import get_internal_negative_control_id_from_lims


def test_get_internal_negative_control_id_from_lims(mutant_lims: LimsAPI):
    # GIVEN a sample_internal_id
    sample_internal_id = "sample_qc_pass"

    # WHEN parsing the metadata
    internal_negative_control_id = get_internal_negative_control_id_from_lims(
        lims=mutant_lims, sample_internal_id=sample_internal_id
    )

    # THEN no error is thrown
    assert internal_negative_control_id == "internal_negative_control_qc_pass"
