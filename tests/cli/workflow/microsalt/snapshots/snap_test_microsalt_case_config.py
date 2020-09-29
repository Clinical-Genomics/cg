# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots[
    "test_dry_sample 1"
] = """[
    {
        "CG_ID_project": "microbial_order_test",
        "CG_ID_sample": "microbial_sample_id",
        "Customer_ID": "cust_test",
        "Customer_ID_project": 123456,
        "Customer_ID_sample": "microbial_name_test",
        "application_tag": "dummy_tag",
        "date_arrival": "0001-01-01 00:00:00",
        "date_libprep": "0001-01-01 00:00:00",
        "date_sequencing": "0001-01-01 00:00:00",
        "method_libprep": "1337:00",
        "method_sequencing": "1338:00",
        "organism": "organism_test",
        "priority": "research",
        "reference": "reference_genome_test"
    }
]
"""

snapshots["test_sample 1"] = [
    """[
""",
    """    {
""",
    """        "CG_ID_project": "microbial_order_test",
""",
    """        "CG_ID_sample": "microbial_sample_id",
""",
    """        "Customer_ID": "cust_test",
""",
    """        "Customer_ID_project": 123456,
""",
    """        "Customer_ID_sample": "microbial_name_test",
""",
    """        "application_tag": "dummy_tag",
""",
    """        "date_arrival": "0001-01-01 00:00:00",
""",
    """        "date_libprep": "0001-01-01 00:00:00",
""",
    """        "date_sequencing": "0001-01-01 00:00:00",
""",
    """        "method_libprep": "1337:00",
""",
    """        "method_sequencing": "1338:00",
""",
    """        "organism": "organism_test",
""",
    """        "priority": "research",
""",
    """        "reference": "reference_genome_test"
""",
    """    }
""",
    "]",
]

snapshots[
    "test_dry_sample_order 1"
] = """[
    {
        "CG_ID_project": "microbial_order_test",
        "CG_ID_sample": "microbial_sample_id",
        "Customer_ID": "cust_test",
        "Customer_ID_project": 123456,
        "Customer_ID_sample": "microbial_name_test",
        "application_tag": "dummy_tag",
        "date_arrival": "0001-01-01 00:00:00",
        "date_libprep": "0001-01-01 00:00:00",
        "date_sequencing": "0001-01-01 00:00:00",
        "method_libprep": "1337:00",
        "method_sequencing": "1338:00",
        "organism": "organism_test",
        "priority": "research",
        "reference": "reference_genome_test"
    }
]
"""

snapshots[
    "test_dry_order 1"
] = """[
    {
        "CG_ID_project": "microbial_order_test",
        "CG_ID_sample": "microbial_sample_id",
        "Customer_ID": "cust_test",
        "Customer_ID_project": 123456,
        "Customer_ID_sample": "microbial_name_test",
        "application_tag": "dummy_tag",
        "date_arrival": "0001-01-01 00:00:00",
        "date_libprep": "0001-01-01 00:00:00",
        "date_sequencing": "0001-01-01 00:00:00",
        "method_libprep": "1337:00",
        "method_sequencing": "1338:00",
        "organism": "organism_test",
        "priority": "research",
        "reference": "reference_genome_test"
    }
]
"""
