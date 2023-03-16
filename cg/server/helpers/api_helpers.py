from cg.store.models import Pool, Customer
from typing import List, Optional
from cg.server.ext import db


def get_pools_to_render(customers: Optional[List[Customer]], enquiry: str = None) -> List[Pool]:
    pools: List[Pool] = (
        db.get_pools_by_customer_id(customers=customers) if customers else db.get_pools()
    )
    if enquiry:
        pools: List[Pool] = list(
            set(
                db.get_pools_by_name_enquiry(name_enquiry=enquiry)
                & set(db.get_pools_by_order_enquiry(order_enquiry=enquiry))
            )
        )
    return pools
