# -*- coding: utf-8 -*-
from copy import deepcopy

from . import base, scout

schema_sample = {
    "title": "Sample",
    "type": "object",
    "properties": {
        "name": {
            "type": "string"
        },
    },
    "required": ["name"]
}
schema_sample["properties"].update(scout.sample_properties)
schema_sample["properties"]["exclude_analysis"] = {
    "type": "boolean"
}

schema_family = deepcopy(base.schema_family)
schema_family["properties"].update({
    "keep_vis": {
        "type": "boolean"
    },
    "samples": {
        "type": "array",
        "items": schema_sample
    }
})

schema_project = deepcopy(base.schema_project)
schema_project["properties"].update({
    "families": {
        "type": "array",
        "items": schema_family
    }
})
