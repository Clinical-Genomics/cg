from cg.meta.orders.ticket_handler import TicketHandler


def test_parse_ticket_number(ticket_number: int):
    # GIVEN a string with a ticket number
    order_name = f"#{ticket_number}"

    # WHEN parsing the string
    result = TicketHandler.parse_ticket_number(order_name)

    # THEN assert that the correct string was parsed
    assert result == ticket_number


def test_add_user_name_message(ticket_handler: TicketHandler):
    # GIVEN a message string
    message = ""
    application: str = "apptag"

    # WHEN adding the apptag string
    message = ticket_handler.add_sample_apptag_to_message(message=message, application=application)

    # THEN assert that the apptag was added
    assert application in message
