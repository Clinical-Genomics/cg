# -*- coding: utf-8 -*-
from copy import deepcopy

from . import base, constants

schema_sample = deepcopy(base.schema_sample)
sample_properties = {
    "sex": {
        "enum": constants.SEXES
    },
    "status": {
        "enum": constants.STATUSES
    },
    "father": {
        "type": "string"
    },
    "mother": {
        "type": "string"
    }
}
schema_sample["properties"].update(sample_properties)
schema_sample["required"] = ["name", "sex", "status", "application_tag"]

schema_family = deepcopy(base.schema_family)
schema_family["properties"].update({
    "priority": {
        "enum": constants.PRIORITIES
    },
    "require_qcok": {
        "type": "boolean"
    },
    "samples": {
        "type": "array",
        "items": schema_sample
    }
})
schema_family["required"] = ["name", "priority", "panels"]

schema_project = deepcopy(base.schema_project)
schema_project["properties"].update({
    "families": {
        "type": "array",
        "items": schema_family
    }
})
