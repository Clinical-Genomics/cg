"""Module for building the rsync command to send files to customer inbox on caesar"""

from cg.store import Store


class RsyncAPI:
    def __init__(self, store: Store):
        self.store: Store = store

    def get_case_object(self, ticket_id: int) -> object:
        cases = self.store.get_cases_from_ticket(ticket_id=ticket_id).all()
        case_obj = cases[0]
        return case_obj

    def get_case_id(self, ticket_id: int) -> str:
        case_obj = self.get_case_object(ticket_id=ticket_id)
        case_id = case_obj.internal_id
        return case_id

    def get_customer_id(self, ticket_id: int) -> str:
        case_obj = self.get_case_object(ticket_id=ticket_id)
        customer_id = case_obj.customer.internal_id
        return customer_id

    def generate_rsync_command(self, ticket_id: int, paths: dict) -> str:
        customer_id = self.get_customer_id(ticket_id=ticket_id)
        destination_path = paths["destination_path"] % (customer_id, ticket_id)
        source_path = (
            paths["base_source_path"] + "/" + customer_id + "/inbox/" + str(ticket_id) + "/ "
        )
        rsync_string = "rsync -rvL "
        cmd = rsync_string + source_path + destination_path
        return cmd

    def generate_covid_rsync_command(self, ticket_id: int, paths: dict) -> str:
        case_id = self.get_case_id(ticket_id=ticket_id)
        source_path = paths["covid_source_path"] % (case_id, ticket_id)
        customer_id = self.get_customer_id(ticket_id=ticket_id)
        destination_path = paths["covid_destination_path"] % customer_id
        rsync_string = "rsync -rvL "
        cmd = rsync_string + source_path + destination_path
        return cmd
