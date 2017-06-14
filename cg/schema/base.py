# -*- coding: utf-8 -*-
from . import constants

schema_project = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "Project",
    "description": "Submission of new samples to Clinical Genomics",
    "type": "object",
    "properties": {
        "name": {
            "type": "string"
        },
        "customer": {
            "description": "Clinical Genomics customer identifier",
            "enum": constants.CUSTOMERS,
        },
    },
    "required": ["name", "customer"]
}

schema_family = {
    "title": "Family",
    "type": "object",
    "properties": {
        "name": {
            "description": "Family name used to identify analyses e.g. in Scout",
            "type": "string"
        },
        "panels": {
            "description": "Default gene panels to use for analysis",
            "type": "array",
            "items": {
                "enum": constants.PANELS,
            },
            "uniqueItems": True
        }
    },
    "required": ["name"]
}

schema_sample = {
    "title": "Sample",
    "type": "object",
    "properties": {
        "name": {
            "type": "string"
        },
        "application_tag": {
            "description": "Clinical Genomics application code",
            "type": "string"
        },
        "source": {
            "enum": constants.SOURCES
        },
        "tumour": {
            "type": "boolean"
        },
        "container": {
            "enum": constants.CONTAINERS
        },
        "container_name": {
            "type": "string"
        },
        "well_position": {
            "type": "string",
            "pattern": "^[A-Z]:[1-9]{1,2}$"
        },
        "quantity": {
            "type": "number"
        },
        "comment": {
            "type": "string"
        }
    },
    "required": ["name", "application_tag"]
}
