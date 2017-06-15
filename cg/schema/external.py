# -*- coding: utf-8 -*-
from copy import deepcopy

from . import constants, scout

schema_project = deepcopy(scout.schema_project)
schema_family = schema_project["properties"]["families"]["items"]
del schema_family["properties"]["require_qcok"]
del schema_family["properties"]["priority"]
schema_family["required"] = ["name", "panels"]
schema_sample = schema_family["properties"]["samples"]["items"]
del schema_sample["properties"]["container"]
del schema_sample["properties"]["container_name"]
del schema_sample["properties"]["quantity"]
del schema_sample["properties"]["source"]
del schema_sample["properties"]["well_position"]
schema_sample["properties"]["capture_kit"] = {
    "enum": constants.CAPTURE_KITS
}
