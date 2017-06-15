# -*- coding: utf-8 -*-
from copy import deepcopy

from . import base

schema_project = deepcopy(base.schema_project)
schema_project["properties"].update({
    "samples": {
        "type": "array",
        "items": base.schema_sample
    }
})
