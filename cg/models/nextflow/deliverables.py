import collections

from pydantic.v1 import BaseModel, validator

from cg.constants.nextflow import DELIVER_FILE_HEADERS


def replace_dict_values(replace_map: dict, my_dict: dict) -> dict:
    for str_to_replace, with_value in replace_map.items():
        for key, value in my_dict.items():
            if not value:
                value = "~"
            my_dict.update({key: value.replace(str_to_replace, with_value)})
    return my_dict


class NextflowDeliverables(BaseModel):
    """Nextflow deliverables model

    Attributes:
        deliverables: dictionary containing format, path, path_index, step, tag and id keys
    """

    deliverables: dict

    @validator("deliverables")
    def headers(cls, v: dict) -> None:
        """Validate header format."""
        if collections.Counter(list(v.keys())) != collections.Counter(DELIVER_FILE_HEADERS):
            raise ValueError(
                f"Headers are not matching the standard header format: {DELIVER_FILE_HEADERS}"
            )
        for key, value in v.items():
            if not value and key != "path_index":
                raise ValueError("An entry other than path_index is empty!")
