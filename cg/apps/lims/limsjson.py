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


def parse_json(indata: dict) -> dict:
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
