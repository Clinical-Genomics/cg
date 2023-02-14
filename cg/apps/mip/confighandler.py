import logging
from copy import deepcopy

from cg.constants import DEFAULT_CAPTURE_KIT
from cg.constants.subject import RelationshipStatus
from cg.exc import PedigreeConfigError
from marshmallow import Schema, fields, validate

LOG = logging.getLogger(__name__)


class SampleSchema(Schema):
    sample_id = fields.Str(required=True)
    sample_display_name = fields.Str()
    analysis_type = fields.Str(
        required=True,
        validate=validate.OneOf(
            choices=[
                "tga",
                "wes",
                "wgs",
                "wts",
            ]
        ),
    )
    father = fields.Str(default=RelationshipStatus.HAS_NO_PARENT.value)
    mother = fields.Str(default=RelationshipStatus.HAS_NO_PARENT.value)
    phenotype = fields.Str(
        required=True,
        validate=validate.OneOf(choices=["affected", "unaffected", "unknown"]),
    )
    sex = fields.Str(required=True, validate=validate.OneOf(choices=["female", "male", "unknown"]))
    expected_coverage = fields.Float()
    capture_kit = fields.Str(default=DEFAULT_CAPTURE_KIT)


class ConfigSchema(Schema):
    case = fields.Str(required=True)
    default_gene_panels = fields.List(fields.Str(), required=True)
    samples = fields.List(fields.Nested(SampleSchema), required=True)


class ConfigHandler:
    @staticmethod
    def make_pedigree_config(data: dict) -> dict:
        """Make a MIP pedigree config"""
        ConfigHandler.validate_config(data=data)
        return ConfigHandler.parse_pedigree_config(data)

    @staticmethod
    def validate_config(data: dict) -> dict:
        """Validate MIP pedigree config format"""
        errors = ConfigSchema().validate(data)
        fatal_error = False
        for field, messages in errors.items():
            if isinstance(messages, dict):
                for sample_index, sample_errors in messages.items():
                    try:
                        sample_id = data["samples"][sample_index]["sample_id"]
                    except KeyError:
                        raise PedigreeConfigError("missing sample id")
                    for sample_key, sub_messages in sample_errors.items():
                        if sub_messages != ["Unknown field."]:
                            fatal_error = True
                        LOG.error(f"{sample_id} -> {sample_key}: {', '.join(sub_messages)}")
            else:
                fatal_error = True
                LOG.error(f"{field}: {', '.join(messages)}")
        if fatal_error:
            raise PedigreeConfigError("invalid config input", errors=errors)
        return errors

    @staticmethod
    def parse_pedigree_config(data: dict) -> dict:
        """Parse the pedigree config data"""
        data_copy = deepcopy(data)
        # handle single sample cases with 'unknown' phenotype
        if len(data_copy["samples"]) == 1 and data_copy["samples"][0]["phenotype"] == "unknown":
            LOG.info("setting 'unknown' phenotype to 'unaffected'")
            data_copy["samples"][0]["phenotype"] = "unaffected"
        for sample_data in data_copy["samples"]:
            sample_data["mother"] = (
                sample_data.get("mother") or RelationshipStatus.HAS_NO_PARENT.value
            )
            sample_data["father"] = (
                sample_data.get("father") or RelationshipStatus.HAS_NO_PARENT.value
            )
            if sample_data["analysis_type"] == "wgs" and sample_data.get("capture_kit") is None:
                sample_data["capture_kit"] = DEFAULT_CAPTURE_KIT
        return data_copy
