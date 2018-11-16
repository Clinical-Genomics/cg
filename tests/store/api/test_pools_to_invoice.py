from datetime import datetime as dt
from cg.store import Store


def test_pools_to_invoice(store: Store):

    # GIVEN a valid customer and a valid application_version 

    customer_group = store.add_customer_group('dummy_group', 'dummy group')
    new_customer = store.add_customer(internal_id = 'cust000', name = 'Test customer',
                                        scout_access = True, customer_group = customer_group, 
                                        invoice_address = 'skolgatan 15',  invoice_reference = 'abc')
    store.add_commit(new_customer)

    application = store.add_application('RMLS05R150', 'rml', 'Ready-made', sequencing_depth=0)
    store.add_commit(application)
    
    app_version = store.add_version(application = application, version = 1, valid_from = dt.today(),
                    prices = {'standard':12, 'priority':222, 'express':123, 'research':12})
    store.add_commit(app_version)

    # WHEN adding a new pool into the database
    new_pool = store.add_pool(customer = new_customer, name = 'Test', order =  'Test', ordered = dt.today(),
                 application_version = app_version)
    store.add_commit(new_pool)    

    # THEN the new pool should have no_invoice = False
    pool = store.pools(customer=None).first()
    assert  pool.no_invoice == False


