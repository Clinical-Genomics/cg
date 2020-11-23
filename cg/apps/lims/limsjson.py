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

    project_type = None
    data_analyses = set(sample["data_analysis"].lower() for sample in samples)

    if len(data_analyses) == 1:
        data_analysis = data_analyses.pop()

        # print(f"{data_analysis=}")

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


def expand_case(case_id, parsed_case):
    """Fill-in information about families."""
    new_case = {"name": case_id, "samples": []}
    # print("parsed_case: ", parsed_case)
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

    # print("new_case: ", new_case)

    return new_case


def parse_json_old(indata: dict) -> dict:
    """Parse JSON from LIMS export."""
    data = {
        "project_type": str(Pipeline.MIP_DNA),
        "customer": indata["customer"].lower(),
        "name": indata.get("name"),
        "comment": indata.get("comment"),
        "items": [],
    }
    families = {}
    for sample_data in indata["samples"]:
        if sample_data["family_name"] not in families:
            families[sample_data["family_name"]] = []
        families[sample_data["family_name"]].append(sample_data)

    for family_name, samples in families.items():
        family_data = {"name": family_name, "samples": []}
        require_qcoks = set(sample.get("require_qcok", False) for sample in samples)
        if True in require_qcoks:
            family_data["require_qcok"] = True

        priorities = set(sample["priority"].lower() for sample in samples)
        if "express" in priorities:
            family_data["priority"] = "express"
        elif "priority" in priorities:
            family_data["priority"] = "priority"
        else:
            family_data["priority"] = priorities.pop()

        panels = set()
        for sample in samples:
            panels.update(sample["panels"])
            sample_data = {
                "name": sample["name"],
                "sex": sample["sex"],
                "application": sample["application"],
                "source": sample["source"],
                "container": sample["container"],
                "data_analysis": sample.get("data_analysis", str(Pipeline.MIP_DNA)),
            }
            well_position_raw = sample.get("well_position")
            if well_position_raw:
                sample_data["well_position"] = (
                    ":".join(well_position_raw)
                    if ":" not in well_position_raw
                    else well_position_raw
                )
            for key in OPTIONAL_KEYS:
                if sample.get(key):
                    sample_data[key] = sample[key]
            family_data["samples"].append(sample_data)
        family_data["panels"] = list(panels)
        data["items"].append(family_data)

    return data
