import click
from cg.apps import tb
from tabulate import tabulate
from colorclass import Color

from cg.store import Store
from cg.constants import FAMILY_ACTIONS, PRIORITY_OPTIONS

STATUS_OPTIONS = ["pending", "running", "completed", "failed", "error"]
CASE_HEADERS_LONG = [
    "Case",
    "Workflow",
    "Ordered",
    "Received",
    "Prepared",
    "Sequenced",
    "Flowcells",
    "Analysed",
    "Uploaded",
    "Delivered",
    "Delivery Reported",
    "Invoiced",
    "TAT",
]
ALWAYS_LONG_HEADERS = [
    CASE_HEADERS_LONG[0],
    CASE_HEADERS_LONG[1],
    CASE_HEADERS_LONG[6],
    CASE_HEADERS_LONG[7],
]
CASE_HEADERS_MEDIUM = []
CASE_HEADERS_SHORT = []

for header in CASE_HEADERS_LONG:

    if header not in ALWAYS_LONG_HEADERS:
        header = header[:3]

    CASE_HEADERS_MEDIUM.append(header)

    if header not in ALWAYS_LONG_HEADERS:
        header = header[0]

    CASE_HEADERS_SHORT.append(header)


@click.group()
@click.pass_context
def status(context):
    """View status of things."""
    context.obj["status_db"] = Store(context.obj["database"])


@status.command()
@click.pass_context
def analysis(context):
    """Which families will be analyzed?"""
    records = context.obj["status_db"].cases_to_analyze(pipeline="mip")
    for family_obj in records:
        click.echo(family_obj)


def present_bool(a_dict, param, show_false=False):
    """presents boolean value in a human friendly format"""
    value = a_dict.get(param)

    if show_false:
        return (
            "-"
            if value is None
            else "✓"
            if value is True
            else "✗"
            if value is False
            else str(value)
        )

    return "-" if value is None else "✓" if value is True else "" if value is False else str(value)


def present_date(a_dict, param, show_negative, show_time):
    """presents datetime value in a human friendly format"""
    value = a_dict.get(param)

    if not show_time and value and value.date:
        value = value.date()

    if show_negative:
        return str(value)

    return "" if not value else value if value else str(value)


def present_string(a_dict, param, show_negative):
    """presents string value in a human friendly format"""
    value = a_dict.get(param)

    if show_negative:
        return str(value)

    return "" if not value else value if value else str(value)


@status.command()
@click.pass_context
@click.option(
    "-o",
    "--output",
    "output_type",
    type=click.Choice(["bool", "count", "date", "datetime"]),
    default="bool",
    help="how to display status",
)
@click.option("--verbose", is_flag=True, help="show status information otherwise left out")
@click.option("--days", default=31, help="days to go back")
@click.option("--internal-id", help="search by internal id")
@click.option("--name", help="search by name given by customer")
@click.option("--case-action", type=click.Choice(FAMILY_ACTIONS), help="filter by case action")
@click.option("--priority", type=click.Choice(PRIORITY_OPTIONS), help="filter by priority")
@click.option("--data-analysis", help="filter on case data_analysis")
@click.option("--sample-id", help="filter by sample id")
@click.option("-c", "--customer-id", help="filter by customer")
@click.option("-C", "--exclude-customer-id", help="exclude customer")
@click.option("-r", "--only-received", is_flag=True, help="only completely received cases")
@click.option("-R", "--exclude-received", is_flag=True, help="exclude completely received cases")
@click.option("-p", "--only-prepared", is_flag=True, help="only completely prepared cases")
@click.option("-P", "--exclude-prepared", is_flag=True, help="exclude completely prepared cases")
@click.option("-s", "--only-sequenced", is_flag=True, help="only completely sequenced cases")
@click.option("-S", "--exclude-sequenced", is_flag=True, help="exclude completely sequenced cases")
@click.option("-a", "--only-analysed", is_flag=True, help="only analysed cases")
@click.option("-A", "--exclude-analysed", is_flag=True, help="exclude analysed cases")
@click.option("-u", "--only-uploaded", is_flag=True, help="only uploaded cases")
@click.option("-U", "--exclude-uploaded", is_flag=True, help="exclude uploaded cases")
@click.option("-d", "--only-delivered", is_flag=True, help="only LIMS delivered cases")
@click.option("-D", "--exclude-delivered", is_flag=True, help="exclude LIMS delivered cases")
@click.option("--dr", "--only-delivery-reported", is_flag=True, help="only delivery reported cases")
@click.option(
    "--DR", "--exclude-delivery-reported", is_flag=True, help="exclude delivery " "reported cases"
)
@click.option("-i", "--only-invoiced", is_flag=True, help="only completely invoiced cases")
@click.option("-I", "--exclude-invoiced", is_flag=True, help="exclude completely invoiced cases")
def cases(
    context,
    output_type,
    verbose,
    days,
    internal_id,
    name,
    case_action,
    priority,
    customer_id,
    data_analysis,
    sample_id,
    only_received,
    only_prepared,
    only_sequenced,
    only_analysed,
    only_uploaded,
    only_delivered,
    only_delivery_reported,
    only_invoiced,
    exclude_customer_id,
    exclude_received,
    exclude_prepared,
    exclude_sequenced,
    exclude_analysed,
    exclude_uploaded,
    exclude_delivered,
    exclude_delivery_reported,
    exclude_invoiced,
):
    """progress of each case"""
    records = context.obj["status_db"].cases(
        days=days,
        internal_id=internal_id,
        name=name,
        case_action=case_action,
        priority=priority,
        customer_id=customer_id,
        exclude_customer_id=exclude_customer_id,
        data_analysis=data_analysis,
        sample_id=sample_id,
        only_received=only_received,
        only_prepared=only_prepared,
        only_sequenced=only_sequenced,
        only_analysed=only_analysed,
        only_uploaded=only_uploaded,
        only_delivered=only_delivered,
        only_delivery_reported=only_delivery_reported,
        only_invoiced=only_invoiced,
        exclude_received=exclude_received,
        exclude_prepared=exclude_prepared,
        exclude_sequenced=exclude_sequenced,
        exclude_analysed=exclude_analysed,
        exclude_uploaded=exclude_uploaded,
        exclude_delivered=exclude_delivered,
        exclude_delivery_reported=exclude_delivery_reported,
        exclude_invoiced=exclude_invoiced,
    )
    case_rows = []

    if output_type == "bool":
        case_header = CASE_HEADERS_SHORT

    elif output_type == "count":
        case_header = CASE_HEADERS_MEDIUM

    elif output_type in ("date", "datetime"):
        case_header = CASE_HEADERS_LONG

    for case in records:

        tat_number = case.get("tat")
        max_tat = case.get("max_tat")

        if (
            case.get("samples_received_bool")
            and case.get("samples_delivered_bool")
            and tat_number <= max_tat
        ):
            tat_color = "green"
        elif tat_number == max_tat:
            tat_color = "yellow"
        elif tat_number > max_tat:
            tat_color = "red"
        else:
            tat_color = "white"

        color_start = Color("{" + f"{tat_color}" + "}")
        color_end = Color("{/" + f"{tat_color}" + "}")

        if (
            not case.get("case_external_bool")
            and case.get("samples_received_bool")
            and case.get("samples_delivered_bool")
        ):
            tat = f"{tat_number}/{max_tat}" + color_end
        elif case.get("case_external_bool") and case.get("analysis_uploaded_bool"):
            tat = f"{tat_number}/{max_tat}" + color_end
        else:
            tat = f"({tat_number})/{max_tat}" + color_end

        title = color_start + f"{case.get('internal_id')}"

        if name:
            title = f"{title} ({case.get('name')})"

        data_analysis = f"{case.get('data_analysis')}"

        show_time = output_type == "datetime"

        ordered = present_date(case, "ordered_at", verbose, show_time)

        if output_type == "bool":
            received = present_bool(case, "samples_received_bool", verbose)
            prepared = present_bool(case, "samples_prepared_bool", verbose)
            sequenced = present_bool(case, "samples_sequenced_bool", verbose)
            flowcell = present_bool(case, "flowcells_on_disk_bool", verbose)
            analysed_bool = present_bool(case, "analysis_completed_bool", verbose)

            if case.get("analysis_completed_at"):
                analysed = f"{analysed_bool}"
            elif case.get("analysis_status"):
                analysed = (
                    f"{analysed_bool}{present_string(case, 'analysis_status',verbose)}"
                    f" {case.get('analysis_completion')}%"
                )
            else:
                analysed = f"{analysed_bool}{present_string(case, 'case_action', verbose)}"

            uploaded = present_bool(case, "analysis_uploaded_bool", verbose)
            delivered = present_bool(case, "samples_delivered_bool", verbose)
            delivery_reported = present_bool(case, "analysis_delivery_reported_bool", verbose)
            invoiced = present_bool(case, "samples_invoiced_bool", verbose)

        elif output_type == "count":
            received = f"{case.get('samples_received')}/{case.get('samples_to_receive')}"
            prepared = f"{case.get('samples_prepared')}/{case.get('samples_to_prepare')}"
            sequenced = f"{case.get('samples_sequenced')}/{case.get('samples_to_sequence')}"
            flowcell = f"{case.get('flowcells_on_disk')}/{case.get('total_samples')}"

            if case.get("analysis_completed_at"):
                analysed = f"{present_date(case, 'analysis_completed_at', verbose, show_time)}"
            elif case.get("analysis_status"):
                analysed = (
                    f"{present_string(case, 'analysis_status', verbose)}"
                    f" {case.get('analysis_completion')}%"
                )
            else:
                analysed = f"{present_string(case, 'case_action', verbose)}"

            uploaded = present_date(case, "analysis_uploaded_at", verbose, show_time)
            delivered = f"{case.get('samples_delivered')}/{case.get('samples_to_deliver')}"
            delivery_reported = present_date(
                case, "analysis_delivery_reported_at", verbose, show_time
            )
            invoiced = f"{case.get('samples_invoiced')}/{case.get('samples_to_invoice')}"

        elif output_type in ("date", "datetime"):
            received = present_date(case, "samples_received_at", verbose, show_time)
            prepared = present_date(case, "samples_prepared_at", verbose, show_time)
            sequenced = present_date(case, "samples_sequenced_at", verbose, show_time)
            flowcell = present_string(case, "flowcells_status", verbose)

            if case.get("analysis_completed_at"):
                analysed = f"{present_date(case, 'analysis_completed_at', verbose, show_time)}"
            elif case.get("analysis_status"):
                analysed = (
                    f"{present_string(case, 'analysis_status', verbose)}"
                    f" {case.get('analysis_completion')}%"
                )
            else:
                analysed = f"{present_string(case, 'case_action', verbose)}"

            uploaded = present_date(case, "analysis_uploaded_at", verbose, show_time)
            delivered = present_date(case, "samples_delivered_at", verbose, show_time)
            delivery_reported = present_date(
                case, "analysis_delivery_reported_at", verbose, show_time
            )
            invoiced = present_date(case, "samples_invoiced_at", verbose, show_time)

        case_row = [
            title,
            data_analysis,
            ordered,
            received,
            prepared,
            sequenced,
            flowcell,
            analysed,
            uploaded,
            delivered,
            delivery_reported,
            invoiced,
            tat,
        ]
        case_rows.append(case_row)

    click.echo(tabulate(case_rows, headers=case_header, tablefmt="psql"))

    header_description = ""
    for i, _ in enumerate(case_header):
        if case_header[i] != CASE_HEADERS_LONG[i]:
            header_description = f"{header_description} {case_header[i]}={CASE_HEADERS_LONG[i]}"
    click.echo(header_description)


@status.command()
@click.option("-s", "--skip", default=0, help="skip initial records")
@click.pass_context
def samples(context, skip):
    """View status of samples."""
    records = context.obj["status_db"].samples().offset(skip).limit(30)
    for record in records:
        message = f"{record.internal_id} ({record.customer.internal_id})"
        if record.sequenced_at:
            color = "green"
            message += f" [SEQUENCED: {record.sequenced_at.date()}]"
        elif record.received_at and record.reads:
            color = "orange"
            message += f" [READS: {record.reads}]"
        elif record.received_at:
            color = "blue"
            message += f" [RECEIVED: {record.received_at.date()}]"
        else:
            color = "white"
            message += " [NOT RECEIVED]"
        click.echo(click.style(message, fg=color))


@status.command()
@click.option("-s", "--skip", default=0, help="skip initial records")
@click.pass_context
def families(context, skip):
    """View status of families."""
    click.echo("red: prio > 1, blue: prio = 1, green: completed, yellow: action")
    records = context.obj["status_db"].families().offset(skip).limit(30)
    for family_obj in records:
        color = "red" if family_obj.priority > 1 else "blue"
        message = f"{family_obj.internal_id} ({family_obj.priority})"
        if family_obj.analyses:
            message += f" {family_obj.analyses[0].completed_at.date()}"
            color = "green"
        if family_obj.action:
            message += f" [{family_obj.action.upper()}]"
            color = "yellow"
        click.echo(click.style(message, fg=color))
