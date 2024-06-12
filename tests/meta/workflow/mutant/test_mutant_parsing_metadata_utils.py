from cg.meta.workflow.mutant.metadata_parser.utils import get_internal_negative_control_id_from_lims

# def get_negative_controls_from_list(samples: list[LimsSample]) -> list[LimsSample]:
#     """Filter and return a list of internal negative controls from a given sample list."""
#     negative_controls = []
#     for sample in samples:
#         if sample.udf.get("Control") == "negative" and sample.udf.get("customer") == "cust000":
#             negative_controls.append(sample)
#     return negative_controls


def test_get_internal_negative_control_id_from_lims(mutant_lims):
    # GIVEN a sample_internal_id
    sample_internal_id = "sample_qc_pass"

    # WHEN parsing the metadata
    internal_negative_control_id = get_internal_negative_control_id_from_lims(
        lims=mutant_lims, sample_internal_id=sample_internal_id
    )

    # THEN no error is thrown
    assert internal_negative_control_id == "internal_negative_control_qc_pass"

# def get_internal_negative_control_id(lims: LimsAPI, metadata_for_case: SampleMetadata) -> str:
#     """Query lims to retrive internal_negative_control_id."""
#     sample_internal_id = list(metadata_for_case.keys())[0]  # internal_id of sample from covid pool

#     print(sample_internal_id)

#     internal_negative_control_id = get_internal_negative_control_id_from_lims(
#         lims, sample_internal_id
#     )

#     return internal_negative_control_id
