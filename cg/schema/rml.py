# -*- coding: utf-8 -*-
from copy import deepcopy

from . import base, constants

schema_sample = deepcopy(base.schema_sample)
schema_sample["properties"].update({
    "pool": {
        "type": "string"
    },
    "volume": {
        "description": "Volume (uL)",
        "type": "integer",
        "minimum": 0
    },
    "concentration": {
        "description": "Concentration (nM)",
        "type": "integer",
        "minimum": 0
    },
    "index": {
        "enum": constants.INDEX
    },
    "index_number": {
        "type": "integer",
        "minimum": 0
    }
})
schema_sample["required"] = ["name", "pool", "application_tag"]
schema_sample["properties"]["application_tag"]["enum"] = [
    "RMLP10R150",
    "RMLS05R150",
    "RMLP10R300",
    "RMLS05R300"
]

schema_project = deepcopy(base.schema_project)
schema_project["properties"]["samples"] = {
    "type": "array",
    "items": schema_sample
}
