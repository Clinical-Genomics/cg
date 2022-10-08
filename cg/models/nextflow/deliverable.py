from pydantic import BaseModel, validator
from cg.constants.constants import DELIVER_FILE_HEADERS
import collections


def replace_dict_values(replace_map: dict, my_dict: dict) -> dict:
    for str_to_replace, with_value in replace_map.items():
        for key, value in my_dict.items():
            if not value:
                value = "~"
            my_dict.update({key: value.replace(str_to_replace, with_value)})
    return my_dict


class NextflowDeliverable(BaseModel):
    """Nextflow deliverable model

    Attributes:
        deliverables: dictionary containing format, path, paht_index, step, tag and id keys
    """

    deliverables: dict

    @validator("deliverables")
    def headers(cls, v: dict) -> str:
        if collections.Counter(list(v.keys())) != collections.Counter(DELIVER_FILE_HEADERS):
            raise ValueError(
                f"Headers are not matching the standard header format: {DELIVER_FILE_HEADERS}"
            )
        for key, value in v.items():
            if not value and key != "path_index":
                raise ValueError("An entry other than path_index is empty!")
