from cg.apps.lims.orderform import CASE_PROJECT_TYPES, expand_case
from cg.exc import OrderFormError
from cg.meta.orders.status import StatusHandler
from cg.constants import Pipeline

OPTIONAL_KEYS = (
    "container_name",
    "quantity",
    "volume",
    "concentration",
    "status",
    "comment",
    "capture_kit",
    "mother",
    "father",
)


def get_project_type(samples):
    """Determine the project type."""

    data_analyses = set(sample["data_analysis"].lower() for sample in samples)

    if len(data_analyses) == 1:
        data_analysis = data_analyses.pop()

        if data_analysis == "mip-dna":
            project_type = "mip-dna"
        elif data_analysis == "fluffy":
            project_type = "rml"
        else:
            raise OrderFormError(f"Unsupported json orderform: {data_analysis}")
    else:
        raise OrderFormError(f"mixed 'Data Analysis' types: {', '.join(data_analyses)}")

    return project_type


def parse_json(indata: dict) -> dict:
    """Parse JSON from LIMS export."""

    raw_samples = indata.get("samples")

    if len(raw_samples) == 0:
        raise OrderFormError("orderform doesn't contain any samples")

    parsed_samples = [raw_sample for raw_sample in raw_samples]
    project_type = get_project_type(parsed_samples)
    customer_id = indata.get("customer")
    comment = indata.get("comment")

    if project_type in CASE_PROJECT_TYPES:
        parsed_cases = StatusHandler.group_cases(parsed_samples)
        items = []
        for case_id, parsed_case in parsed_cases.items():
            case_data = expand_case(case_id, parsed_case)
            items.append(case_data)
    else:
        items = parsed_samples

    data = {
        "customer": customer_id,
        "items": items,
        "project_type": project_type,
        "comment": comment,
    }

    return data


def expand_case(case_id: str, parsed_case: dict) -> dict:
    """Fill-in information about families."""
    new_case = {"name": case_id, "samples": []}
    samples = parsed_case

    require_qcoks = set(raw_sample["require_qcok"] for raw_sample in samples)
    new_case["require_qcok"] = True in require_qcoks

    priorities = set(raw_sample["priority"] for raw_sample in samples)
    if len(priorities) == 1:
        new_case["priority"] = priorities.pop()
    else:
        raise OrderFormError(f"multiple values for 'Priority' for case: {case_id}")

    gene_panels = set()
    for raw_sample in samples:
        if raw_sample["panels"]:
            gene_panels.update(raw_sample["panels"])
        new_sample = {}
        for key, value in raw_sample.items():
            if key not in ["panels"]:
                new_sample[key] = value

        new_case["samples"].append(new_sample)

    new_case["panels"] = list(gene_panels)

    return new_case
