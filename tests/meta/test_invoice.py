import mock


from cg.meta.invoice import InvoiceAPI

from cg.constants.invoice import CostCenters
from cg.constants.sequencing import RecordType
from cg.constants.priority import PriorityTerms
from cg.store.models import Pool, Sample

from cg.models.invoice.invoice import InvoiceInfo


def test_instantiate_invoice_api(get_invoice_api_sample):
    # GIVEN a sample invoice api

    # When instantiating
    sample_invoice_api: InvoiceAPI = get_invoice_api_sample

    # THEN return an InvoiceAPI instance
    assert isinstance(sample_invoice_api, InvoiceAPI)


def test_assert_invoice_api(get_invoice_api_sample):
    # GIVEN an invoice API
    api: InvoiceAPI = get_invoice_api_sample
    # THEN a report should be generated
    report = api.get_invoice_report(CostCenters.ki)
    assert type(report) == dict


def test_invoice_api_sample(get_invoice_api_sample, record_type: str = RecordType.Sample):
    """Test that the invoice records the right record_type"""
    # THEN calling InvoiceAPI should return an API
    api: InvoiceAPI = get_invoice_api_sample
    assert api
    # THEN record_type should be Sample
    assert api.record_type == record_type
    # THEN prepare_invoice_report should set priority to standard
    api.get_invoice_report(CostCenters.ki)
    assert api.invoice_info.priority == PriorityTerms.STANDARD

    # THEN get_invoice_report returns a dictionary
    invoice_dict: dict = api.get_invoice_report(CostCenters.ki)
    assert type(invoice_dict) == dict

    # THEN prepare_invoice_report should set priority to standard
    assert api.invoice_info.priority == PriorityTerms.STANDARD

    # THEN raw.records should contain a Pool
    assert type(api.raw_records[0]) == Sample

    # THEN api holds an InvoiceInfo class
    assert type(api.invoice_info) == InvoiceInfo


def test_invoice_api_nipt_customer(
    get_invoice_api_nipt_customer, record_type: str = RecordType.Pool
):
    # GIVEN an invoice api with NIPT customer
    api: InvoiceAPI = get_invoice_api_nipt_customer

    # THEN record_type should be a Pool
    api.genologics_lims = mock.MagicMock()
    assert api.record_type == record_type

    # THEN get_invoice_report returns a dictionary
    invoice_dict = api.get_invoice_report(CostCenters.ki)
    assert type(invoice_dict) == dict

    # THEN prepare_invoice_report should set priority to standard
    assert api.invoice_info.priority == PriorityTerms.STANDARD

    # THEN raw.records should contain a Pool
    assert type(api.raw_records[0]) == Pool

    # THEN api holds an InvoiceInfo class
    assert type(api.invoice_info) == InvoiceInfo


def test_invoice_pool_generic_customer(
    get_invoice_api_pool_generic_customer, record_type: str = RecordType.Pool
):
    # GIVEN an invoice API with a pool and a generic customer
    api: InvoiceAPI = get_invoice_api_pool_generic_customer
    assert api
    # THEN record_type should be Pool
    api.genologics_lims = mock.MagicMock()
    assert api.record_type == record_type
    # THEN prepare_invoice_report should set priority to research
    api.get_invoice_report(CostCenters.ki)
    assert api.invoice_info.priority == PriorityTerms.RESEARCH
