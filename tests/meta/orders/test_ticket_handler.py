from cg.meta.orders.ticket_handler import TicketHandler


def test_parse_ticket_number(ticket: str):
    # GIVEN a string with a ticket number
    order_name = f"#{ticket}"

    # WHEN parsing the string
    result = TicketHandler.parse_ticket_number(order_name)

    # THEN assert that the correct string was parsed
    assert result == ticket


def test_add_user_name_message(ticket_handler: TicketHandler):
    # GIVEN a message string
    message = ""
    application: str = "apptag"

    # WHEN adding the apptag string
    message = ticket_handler.add_sample_apptag_to_message(message=message, application=application)

    # THEN assert that the apptag was added
    assert application in message


def test_add_sample_priority_message(ticket_handler: TicketHandler):
    # GIVEN a message string
    message = ""
    priority: str = "prio"

    # WHEN adding the apptag string
    message = ticket_handler.add_sample_priority_to_message(message=message, priority=priority)

    # THEN assert that the priority was added
    assert priority in message
