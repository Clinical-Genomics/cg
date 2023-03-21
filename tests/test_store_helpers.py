"""
Tests for command module
"""


def test_add_microbial_sample(base_store, helpers):
    # GIVEN a base_store

    # WHEN using the helper to add a microbial sample
    sample = helpers.add_microbial_sample(base_store)

    # THEN there should be a sample
    assert sample
    # THEN there should be an organism
    assert sample.organism
    # THEN there should be a case
    assert sample.links
    # THEN there should be a customer
    assert sample.customer
    # THEN there should be an application_version
    assert sample.application_version


def test_add_invoice(base_store, helpers):
    # GIVEN a base_store
    sample = helpers.add_sample(base_store)
    # WHEN using the helper to add an invoice with a sample
    invoice_sample = helpers.ensure_invoice(
        base_store,
        invoice_id=1,
        samples=[sample],
    )

    # THEN there should be an invoice
    assert invoice_sample
