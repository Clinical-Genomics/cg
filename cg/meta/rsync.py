"""Module for building the rsync command to send files to customer inbox on caesar"""

from cg.store import Store


class RsyncAPI:
    def __init__(self, store: Store):
        self.store: Store = store

    def generate_rsync_command(self, ticket_id: int, base_path: str) -> str:
        cases = self.store.get_cases_from_ticket(ticket_id=ticket_id).all()
        case_obj = cases[0]
        customer_id = case_obj.customer.internal_id
        destination_path = "caesar.scilifelab.se:/home/%s/inbox/%s/" % (customer_id, ticket_id)
        source_path = base_path + "/" + customer_id + "/inbox/" + str(ticket_id) + "/ "
        rsync_string = "rsync -rvL --progress "
        cmd = rsync_string + source_path + destination_path
        return cmd
