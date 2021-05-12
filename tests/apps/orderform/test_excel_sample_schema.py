import datetime

import pytest
from pydantic import ValidationError

from cg.constants import DataDelivery
from cg.models.orders.excel_sample import ExcelSample


def test_excel_minimal_sample_schema(minimal_excel_sample: dict):
    """Test instantiate a minimal sample"""
    # GIVEN some simple sample info from the simplest sample possible

    # WHEN creating a excel sample
    excel_sample: ExcelSample = ExcelSample(**minimal_excel_sample)

    # THEN assert that the sample name info was correctly parsed
    assert excel_sample.name == minimal_excel_sample["Sample/Name"]


def test_excel_swedish_priority(minimal_excel_sample: dict):
    """Test instantiate a sample with swedish priority"""
    # GIVEN some sample where the priority is in swedish
    minimal_excel_sample["UDF/priority"] = "förtur"

    # WHEN creating a excel sample
    excel_sample: ExcelSample = ExcelSample(**minimal_excel_sample)

    # THEN assert that the sample priority info was correctly parsed
    assert excel_sample.priority == "priority"


def test_excel_source_type(minimal_excel_sample: dict):
    """Test instantiate a sample with source type"""
    # GIVEN some sample with a known source type
    source_type = "blood"
    minimal_excel_sample["UDF/Source"] = source_type

    # WHEN creating a excel sample
    excel_sample: ExcelSample = ExcelSample(**minimal_excel_sample)

    # THEN assert that the source type info was correctly parsed
    assert excel_sample.source == source_type


def test_excel_unknown_source_type(minimal_excel_sample: dict):
    """Test instantiate a sample with a unknown source type

    ValidationError should be raised since the source type does not exist
    """
    # GIVEN some sample with a known source type
    source_type = "flagalella"
    minimal_excel_sample["UDF/Source"] = source_type

    # WHEN creating a excel sample
    with pytest.raises(ValidationError):
        # THEN assert that a validation error is raised since source does not exist
        excel_sample: ExcelSample = ExcelSample(**minimal_excel_sample)


def test_excel_datetime_to_date_conversion(minimal_excel_sample: dict):
    """Test instantiate a sample with a datetime collection date

    Datetime string should be converted to date
    """
    # GIVEN some sample with a collection date as a datetime-string
    collection_date = "2021-05-05 00:00:00"
    minimal_excel_sample["UDF/Collection Date"] = collection_date

    # WHEN creating a excel sample
    excel_sample: ExcelSample = ExcelSample(**minimal_excel_sample)

    # THEN the collection_date should only contain the date
    assert str(excel_sample.collection_date) == "2021-05-05"


def test_excel_with_panels(minimal_excel_sample: dict):
    """Test instantiate a sample with some gene panels set"""
    # GIVEN some sample with two gene panels in a semi colon separated string
    panel_1 = "OMIM"
    panel_2 = "PID"
    minimal_excel_sample["UDF/Gene List"] = ";".join([panel_1, panel_2])

    # WHEN creating a excel sample
    excel_sample: ExcelSample = ExcelSample(**minimal_excel_sample)

    # THEN assert that the panels was parsed into a list
    assert set(excel_sample.panels) == set([panel_1, panel_2])


def test_mip_rna_sample_is_correct(mip_rna_orderform_sample: dict):
    """Test that a mip rna orderform sample in parsed correct

    This will test if the aliases are mapped to the correct field in the pydantic model
    """
    # GIVEN sample data about a known balsamic sample

    # WHEN parsing the sample
    mip_rna_sample: ExcelSample = ExcelSample(**mip_rna_orderform_sample)

    # THEN assert that the sample information is parsed correct
    assert mip_rna_sample.name == "s1"
    assert mip_rna_sample.container == "96 well plate"
    assert mip_rna_sample.data_analysis == "MIP RNA"
    assert mip_rna_sample.data_delivery.lower() == str(DataDelivery.ANALYSIS_FILES)
    assert mip_rna_sample.application == "RNAPOAR025"
    assert mip_rna_sample.sex == "male"
    # case-id on the case
    # customer on the order (data)
    # require-qc-ok on the case
    assert mip_rna_sample.source == "tissue (FFPE)"

    assert mip_rna_sample.container_name == "plate1"
    assert mip_rna_sample.well_position == "A:1"
    assert mip_rna_sample.tumour is True
    assert mip_rna_sample.quantity == "4"
    assert mip_rna_sample.comment == "other Elution buffer"
    assert mip_rna_sample.from_sample == "s1"
    assert mip_rna_sample.time_point == "0"
