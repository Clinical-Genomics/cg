"""Module to test the ValidationCaseData class."""

from cg.constants.constants import CaseActions
from cg.services.create_validation_cases.validation_case_data import ValidationCaseData
from cg.services.create_validation_cases.validation_data_input import ValidationDataInput

from cg.store.store import Store


def test_validation_case_data(
    store_with_multiple_cases_and_samples: Store,
    case_id_with_multiple_samples: str,
    sample_id_in_multiple_cases: str,
    validation_sample_id: str,
    case_name: str,
):

    # GIVEN a store with cases and samples and a validation data input
    assert store_with_multiple_cases_and_samples.get_case_by_internal_id(
        case_id_with_multiple_samples
    )
    assert store_with_multiple_cases_and_samples.get_sample_by_internal_id(
        sample_id_in_multiple_cases
    )
    validation_data_input = ValidationDataInput(
        case_id=case_id_with_multiple_samples, case_name=case_name
    )

    # WHEN instantiating the validation case data
    validation_case_data = ValidationCaseData(
        status_db=store_with_multiple_cases_and_samples, validation_data_input=validation_data_input
    )

    # THEN the proper validation case and validation sample are generated
    assert validation_case_data.validation_case.name == case_name + "_validation"
    assert not validation_case_data.validation_case.is_compressible
    assert validation_case_data.validation_case.action == CaseActions.HOLD
    for sample in validation_case_data.validation_samples:
        assert sample.internal_id.startswith("VAL")
