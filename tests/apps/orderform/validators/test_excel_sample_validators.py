import pytest

from cg.constants import METAGENOME_SOURCES
from cg.constants.orderforms import REV_SEX_MAP
from cg.models.orders.constants import ExcelSampleAliases
from cg.models.orders.excel_sample import ExcelSample
from cg.models.orders.sample_base import PriorityEnum


def test_collection_date_conversion(mip_rna_orderform_sample: dict):
    """Tests that a sample with Collection Date set to YYYY-MM-DD HH:MM:SS is converted to YYYY-MM-DD."""

    # GIVEN a parsed order form in Excel format with Collection Date set
    mip_rna_orderform_sample[ExcelSampleAliases.COLLECTION_DATE] = "2023-09-29 00:00:00"

    # WHEN converting the sample to an ExcelSample object
    excel_sample: ExcelSample = ExcelSample.model_validate(mip_rna_orderform_sample)

    # THEN the date should have been converted
    assert excel_sample.collection_date == "2023-09-29"


def test_collection_date_none(mip_rna_orderform_sample: dict):
    """Tests that a sample with no Collection Date set is allowed."""

    # GIVEN a parsed order form in Excel format with no Collection Date set (Note that these are parsed as empty strings
    # rather than None
    mip_rna_orderform_sample[ExcelSampleAliases.COLLECTION_DATE] = ""

    # THEN converting the sample to an ExcelSample object should not raise an error
    assert ExcelSample.model_validate(mip_rna_orderform_sample)


def test_concentration_numeric(mip_rna_orderform_sample: dict):
    """Tests that a sample with concentration set to a natural number is allowed."""

    # GIVEN a parsed order form in Excel format with concentration set to a natural number
    mip_rna_orderform_sample[ExcelSampleAliases.CONCENTRATION] = "2"

    # THEN converting the sample to an ExcelSample object should not raise an error
    excel_sample: ExcelSample = ExcelSample.model_validate(mip_rna_orderform_sample)

    assert excel_sample.concentration == "2"


def test_concentration_fraction(mip_rna_orderform_sample: dict):
    """Tests that a sample with concentration set as a fraction is allowed."""

    # GIVEN a parsed order form in Excel format with concentration set to a fraction
    mip_rna_orderform_sample[ExcelSampleAliases.CONCENTRATION] = "0.23"

    # THEN converting the sample to an ExcelSample object should not raise an error
    excel_sample: ExcelSample = ExcelSample.model_validate(mip_rna_orderform_sample)

    # THEN the parsed ExcelSample object should have its concentration set
    assert excel_sample.concentration == "0.23"


def test_concentration_numeric_fraction(mip_rna_orderform_sample: dict):
    """Tests that a sample with numeric concentration set as a float is allowed and converted."""

    # GIVEN a parsed order form in Excel format with concentration set as a float with only zeroes
    mip_rna_orderform_sample[ExcelSampleAliases.CONCENTRATION] = "2.00"

    # THEN converting the sample to an ExcelSample object should not raise an error
    excel_sample: ExcelSample = ExcelSample.model_validate(mip_rna_orderform_sample)

    # THEN the parsed ExcelSample object should have its concentration set without zeroes
    assert excel_sample.concentration == "2"


def test_concentration_alphabetical_fail(mip_rna_orderform_sample: dict):
    """Tests that a sample with non-numeric concentration raises an AttributeError."""

    # GIVEN a parsed order form in Excel format with concentration set with alphabetical characters
    mip_rna_orderform_sample[ExcelSampleAliases.CONCENTRATION] = "2 nM"

    # THEN converting the sample to an ExcelSample object should raise an AttributeError
    with pytest.raises(AttributeError):
        ExcelSample.model_validate(mip_rna_orderform_sample)


def test_concentration_sample_numeric(mip_rna_orderform_sample: dict):
    """Tests that a sample with concentration_sample set to a natural number is allowed."""

    # GIVEN a parsed order form in Excel format with sample concentration set to a natural number
    mip_rna_orderform_sample[ExcelSampleAliases.CONCENTRATION_SAMPLE] = "2"

    # THEN converting the sample to an ExcelSample object should not raise an error
    excel_sample: ExcelSample = ExcelSample.model_validate(mip_rna_orderform_sample)

    # THEN the ExcelSample object should have its concentration sample set to 2
    assert excel_sample.concentration_sample == "2"


def test_concentration_sample_fraction(mip_rna_orderform_sample: dict):
    """Tests that a sample with concentration sample set as a fraction is allowed."""

    # GIVEN a parsed order form in Excel format with concentration sample set to a fraction
    mip_rna_orderform_sample[ExcelSampleAliases.CONCENTRATION_SAMPLE] = "0.23"

    # THEN converting the sample to an ExcelSample object should not raise an error
    excel_sample: ExcelSample = ExcelSample.model_validate(mip_rna_orderform_sample)

    # THEN the parsed ExcelSample object should have its concentration sample set
    assert excel_sample.concentration_sample == "0.23"


def test_concentration_sample_numeric_fraction(mip_rna_orderform_sample: dict):
    """Tests that a sample with numeric concentration sample set as a float is allowed and converted."""

    # GIVEN a parsed order form in Excel format with concentration sample set as a float with only zeroes
    mip_rna_orderform_sample[ExcelSampleAliases.CONCENTRATION_SAMPLE] = "2.00"

    # THEN converting the sample to an ExcelSample object should not raise an error
    excel_sample: ExcelSample = ExcelSample.model_validate(mip_rna_orderform_sample)

    # THEN the parsed ExcelSample object should have its concentration sample set without zeroes
    assert excel_sample.concentration_sample == "2"


def test_concentration_sample_alphabetical_fail(mip_rna_orderform_sample: dict):
    """Tests that a sample with non-numeric concentration sample raises an AttributeError."""

    # GIVEN a parsed order form in Excel format with concentration sample set with alphabetical characters
    mip_rna_orderform_sample[ExcelSampleAliases.CONCENTRATION_SAMPLE] = "2 nM"

    # THEN converting the sample to an ExcelSample object should raise an AttributeError
    with pytest.raises(AttributeError):
        ExcelSample.model_validate(mip_rna_orderform_sample)


def test_data_analysis_valid(mip_rna_orderform_sample: dict):
    """Tests that a sample with a valid data analysis set is allowed."""

    # GIVEN a parsed order form in Excel format with data analysis set to MIP RNA

    # THEN no error should be raised when converting to an ExcelSample object
    assert ExcelSample.model_validate(mip_rna_orderform_sample)


def test_data_analysis_invalid(mip_rna_orderform_sample: dict):
    """Tests that a sample with an invalid data analysis set is not allowed."""

    # GIVEN a parsed order form in Excel format with data analysis set to an invalid value
    mip_rna_orderform_sample[ExcelSampleAliases.DATA_ANALYSIS] = "INVALID ANALYSIS"

    # THEN an AttributeError should be raised when converting to an ExcelSample object
    with pytest.raises(AttributeError):
        ExcelSample.model_validate(mip_rna_orderform_sample)


def test_data_delivery_convert_to_lower(mip_rna_orderform_sample: dict):
    """Tests that a sample with a data delivery which is not all lower case is converted correctly."""

    # GIVEN a parsed order form in Excel format with data delivery set in all caps
    mip_rna_orderform_sample[ExcelSampleAliases.DATA_DELIVERY] = "ANALYSIS"

    # WHEN converting to an ExcelSample object
    excel_sample: ExcelSample = ExcelSample.model_validate(mip_rna_orderform_sample)

    # THEN the data delivery should be in lower case
    assert excel_sample.data_delivery == "analysis"


def test_father_convert_zeroes(mip_rna_orderform_sample: dict):
    """Tests that if 0.0 is provided as father, then None is set instead."""

    # GIVEN a parsed order form in Excel format with 'father' set to 0.0
    mip_rna_orderform_sample[ExcelSampleAliases.FATHER] = "0.0"

    # WHEN converting to an ExcelSample object
    excel_sample: ExcelSample = ExcelSample.model_validate(mip_rna_orderform_sample)

    # THEN 'father' should be set to None
    assert excel_sample.father is None


def test_parse_panels_none(mip_rna_orderform_sample: dict):
    """Tests that the UDF/Gene List is allowed to be none for a sample in an order form."""

    # GIVEN a parsed order form in Excel format with no panels set (Note that these are parsed as empty strings
    # rather than None
    mip_rna_orderform_sample[ExcelSampleAliases.PANELS] = ""

    # THEN the model validation should succeed
    ExcelSample.model_validate(mip_rna_orderform_sample)


def test_parse_panels_semicolon_separator(mip_rna_orderform_sample: dict):
    """Tests that the panel list is split when given with a semicolon separated string."""

    # GIVEN a parsed order form in Excel format with panels separated with a semicolon
    mip_rna_orderform_sample[ExcelSampleAliases.PANELS] = "gene_1;gene_2"

    # WHEN converting to an ExcelSample object
    excel_sample: ExcelSample = ExcelSample.model_validate(mip_rna_orderform_sample)

    assert excel_sample.panels == ["gene_1", "gene_2"]


def test_parse_panels_colon_separator(mip_rna_orderform_sample: dict):
    """Tests that the panel list is split when given with a colon separated string."""

    # GIVEN a parsed order form in Excel format with panels separated with a colon
    mip_rna_orderform_sample[ExcelSampleAliases.PANELS] = "gene_1:gene_2"

    # WHEN converting to an ExcelSample object
    excel_sample: ExcelSample = ExcelSample.model_validate(mip_rna_orderform_sample)

    assert excel_sample.panels == ["gene_1", "gene_2"]


def test_priority_foertur(mip_rna_orderform_sample: dict):
    """Tests that a sample with priority specified to 'förtur', then the validation converts the value to English."""

    # GIVEN a parsed order form in Excel format with priority set to 'förtur'
    mip_rna_orderform_sample[ExcelSampleAliases.PRIORITY] = "förtur"

    # WHEN converting to an ExcelSample object
    excel_sample: ExcelSample = ExcelSample.model_validate(mip_rna_orderform_sample)

    # THEN the priority should be set to 'priority'
    assert excel_sample.priority == PriorityEnum.priority


def test_valid_priority_all_caps(mip_rna_orderform_sample: dict):
    """Tests that a sample with a valid priority specified in all caps is converted to lower case."""

    # GIVEN a parsed order form in Excel format with priority set to "PRIORITY"
    mip_rna_orderform_sample[ExcelSampleAliases.PRIORITY] = "PRIORITY"

    # WHEN converting to an ExcelSample object
    excel_sample: ExcelSample = ExcelSample.model_validate(mip_rna_orderform_sample)

    # THEN the priority should be in lower case
    assert excel_sample.priority == PriorityEnum.priority


def test_priority_foertur_all_caps(mip_rna_orderform_sample: dict):
    """Tests that a sample with priority specified to 'FÖRTUR',
    then the validation converts the value to English and lower case."""

    # GIVEN a parsed order form in Excel format with priority set to 'FÖRTUR'
    mip_rna_orderform_sample[ExcelSampleAliases.PRIORITY] = "FÖRTUR"

    # WHEN converting to an ExcelSample object
    excel_sample: ExcelSample = ExcelSample.model_validate(mip_rna_orderform_sample)

    # THEN the priority should be set to 'priority'
    assert excel_sample.priority == PriorityEnum.priority


def test_valid_priority_with_spaces(mip_rna_orderform_sample: dict):
    """Tests that a sample with a valid priority has its spaces replaced by underscores."""

    # GIVEN a parsed order form in Excel format with priority set to "Clinical trials"
    mip_rna_orderform_sample[ExcelSampleAliases.PRIORITY] = "Clinical trials"

    # WHEN converting to an ExcelSample object
    excel_sample: ExcelSample = ExcelSample.model_validate(mip_rna_orderform_sample)

    # THEN the priority should set to "clinical_trials"
    assert excel_sample.priority == PriorityEnum.clinical_trials


def test_convert_sex_m(mip_rna_orderform_sample: dict):
    """Tests that sex is converted to 'male' if set as 'M'."""

    # GIVEN a parsed order form in Excel format with sex set to 'M'

    # WHEN converting to an ExcelSample object
    excel_sample: ExcelSample = ExcelSample.model_validate(mip_rna_orderform_sample)

    # THEN the sex should be set to 'male'
    assert excel_sample.sex == REV_SEX_MAP["M"]


def test_convert_sex_strip(mip_rna_orderform_sample: dict):
    """Tests that sex is stripped from any trailing spaces."""

    # GIVEN a parsed order form in Excel format with sex set to 'M '
    mip_rna_orderform_sample[ExcelSampleAliases.SEX] = "M "

    # WHEN converting to an ExcelSample object
    excel_sample: ExcelSample = ExcelSample.model_validate(mip_rna_orderform_sample)

    # THEN the sex should have been converted to 'male'
    assert excel_sample.sex == REV_SEX_MAP["M"]


def test_invalid_source(mip_rna_orderform_sample: dict):
    """Tests that a ValueError is raised when an invalid source is specified."""

    # GIVEN a parsed order form in Excel format with an invalid source specified
    mip_rna_orderform_sample[ExcelSampleAliases.SOURCE] = "INVALID SOURCE"

    # WHEN converting to an ExcelSample object

    # THEN a ValueError should be raised
    with pytest.raises(ValueError):
        ExcelSample.model_validate(mip_rna_orderform_sample)


def test_valid_source(mip_rna_orderform_sample: dict):
    """Tests that no ValueError is raised when a valid source is specified."""

    # GIVEN a parsed order form in Excel format with a valid source specified
    mip_rna_orderform_sample[ExcelSampleAliases.SOURCE] = METAGENOME_SOURCES[0]

    # WHEN converting to an ExcelSample object

    # THEN no ValueError should be raised
    ExcelSample.model_validate(mip_rna_orderform_sample)


def test_status_convert_to_lower(mip_rna_orderform_sample: dict):
    """Tests that the given status value is converted to lower case."""

    # GIVEN a parsed order form in Excel format with a valid source specified
    mip_rna_orderform_sample[ExcelSampleAliases.STATUS] = "ANALYSIS"

    # WHEN converting to an ExcelSample object

    # THEN no ValueError should be raised
    excel_sample: ExcelSample = ExcelSample.model_validate(mip_rna_orderform_sample)

    # THEN the status should be in lower case
    assert excel_sample.status == "analysis"


def test_volume_non_numeric(mip_rna_orderform_sample: dict):
    """Tests that an error is raised when specifying a non-numeric volume."""

    # GIVEN a parsed order form in Excel format with non-numeric volume specified
    mip_rna_orderform_sample[ExcelSampleAliases.VOLUME] = "2 nM"

    # WHEN converting to an ExcelSample object

    # THEN an AttributeError should be raised
    with pytest.raises(AttributeError):
        ExcelSample.model_validate(mip_rna_orderform_sample)


def test_volume_positive_integer(mip_rna_orderform_sample: dict):
    """Tests that no error is raised when parsing a volume set to a positive integer."""

    # GIVEN a parsed order form in Excel format with a positive integer volume
    mip_rna_orderform_sample[ExcelSampleAliases.VOLUME] = "2"

    # WHEN converting to an ExcelSample object

    # THEN no AttributeError should be raised
    excel_sample: ExcelSample = ExcelSample.model_validate(mip_rna_orderform_sample)

    # THEN the volume should be unchanged
    assert excel_sample.volume == "2"


def test_volume_decimal_integer(mip_rna_orderform_sample: dict):
    """Tests that an integer given in float format, i.e. 2.0 instead of 2 and so on, is converted to integer format."""

    # GIVEN a parsed order form in Excel format with an integer volume in float format
    mip_rna_orderform_sample[ExcelSampleAliases.VOLUME] = "2.0"

    # WHEN converting to an ExcelSample object

    # THEN no AttributeError should be raised
    excel_sample: ExcelSample = ExcelSample.model_validate(mip_rna_orderform_sample)

    # THEN the volume should be converted to have no decimals
    assert excel_sample.volume == "2"
