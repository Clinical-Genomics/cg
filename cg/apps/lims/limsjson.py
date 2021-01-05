from cg.apps.lims.orderform import CASE_PROJECT_TYPES, expand_case
from cg.constants import DataDelivery
from cg.exc import OrderFormError
from cg.meta.orders.status import StatusHandler


def get_project_type(samples: [dict]) -> str:
    """Determine the project type."""

    data_analyses = set(sample.get("data_analysis", "mip-dna").lower() for sample in samples)

    if len(data_analyses) > 1:
        raise OrderFormError(f"mixed 'Data Analysis' types: {', '.join(data_analyses)}")

    if data_analyses == {"mip-dna"}:
        return "mip-dna"
    elif data_analyses == {"fluffy"}:
        return "fluffy"
    elif data_analyses == {"balsamic"}:
        return "balsamic"

    raise OrderFormError(f"Unsupported order_data orderform: {data_analyses}")


def get_data_delivery(samples: [dict]) -> str:
    """Determine the order_data delivery type."""

    data_deliveries = set(sample.get("data_delivery", "").lower() for sample in samples)

    if len(data_deliveries) > 1:
        raise OrderFormError(f"mixed 'Data Delivery' types: {', '.join(data_deliveries)}")

    if data_deliveries == {""}:
        return ""

    try:
        return str(DataDelivery(data_deliveries.pop()))
    except ValueError:
        raise OrderFormError(f"Unsupported order_data delivery: {data_deliveries}")


def parse_json_order(order_data: dict) -> dict:
    """Parse JSON from LIMS export."""

    samples = order_data.get("samples")

    if not samples:
        raise OrderFormError("orderform doesn't contain any samples")

    project_type = get_project_type(samples)
    data_delivery = get_data_delivery(samples)
    customer_id = order_data["customer"].lower()
    comment = order_data.get("comment")
    order_name = order_data.get("name")

    if project_type in CASE_PROJECT_TYPES:
        parsed_cases = StatusHandler.group_cases(samples)
        items = []
        for case_id, parsed_case in parsed_cases.items():
            case_data = expand_case(case_id, parsed_case)
            items.append(case_data)
    else:
        items = samples

    order_data = {
        "customer": customer_id,
        "items": items,
        "name": order_name,
        "project_type": project_type,
        "delivery": data_delivery,
        "comment": comment,
    }

    return order_data


def expand_case(case_id: str, parsed_case: dict) -> dict:
    """Fill-in information about families."""
    new_case = {"name": case_id, "samples": []}
    samples = parsed_case

    require_qcoks = set(raw_sample["require_qcok"] for raw_sample in samples)
    new_case["require_qcok"] = True in require_qcoks

    priorities = set(raw_sample["priority"].lower() for raw_sample in samples)
    if len(priorities) != 1:
        raise OrderFormError(f"multiple values for 'Priority' for case: {case_id}")
    new_case["priority"] = priorities.pop()

    gene_panels = set()
    for raw_sample in samples:
        if raw_sample.get("panels"):
            gene_panels.update(raw_sample["panels"])

        new_sample = {}
        well_position_raw = raw_sample.get("well_position")
        if well_position_raw:
            new_sample["well_position"] = (
                ":".join(well_position_raw) if ":" not in well_position_raw else well_position_raw
            )

        for key, value in raw_sample.items():
            if key not in ["panels", "well_position"]:
                new_sample[key] = value

        new_case["samples"].append(new_sample)

    if gene_panels:
        new_case["panels"] = list(gene_panels)

    return new_case
