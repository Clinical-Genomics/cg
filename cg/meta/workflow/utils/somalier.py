import copy
from typing import Any

from cg.constants.subject import PlinkSex
from cg.exc import MissingMultiqcSectionError
from cg.models.deliverables.metric_deliverables import MultiqcDataJson
from cg.store.models import Sample


def set_somalier_sex_for_sample(sample: Sample, metric_conditions: dict) -> None:
    if "somalier_sex" in metric_conditions:
        metric_conditions["somalier_sex"]["threshold"] = float(
            {
                "male": PlinkSex.MALE,
                "female": PlinkSex.FEMALE,
                "unknown": PlinkSex.UNKNOWN,
            }[sample.sex]
        )


def get_somalier_dict(multiqc_json: MultiqcDataJson) -> dict[str, Any]:
    raw_data: dict[str, dict] = multiqc_json.report_saved_raw_data or {}

    somalier_section = "multiqc_somalier"
    if somalier_section not in raw_data:
        raise MissingMultiqcSectionError(
            f"Section `{somalier_section}` not found in MultiQC report_saved_raw_data"
        )

    somalier_raw = copy.deepcopy(raw_data[somalier_section])
    for sample_id, metrics in somalier_raw.items():
        somalier_raw[sample_id] = {f"somalier_{k}": v for k, v in metrics.items()}

    return somalier_raw
