from pydantic import BaseModel


class DeliveryFileTags(BaseModel):
    """
    Model to hold the tags for the files to deliver.
    case_tags: The tags for the case files to deliver
    sample_tags: The tags for the sample files to deliver
    """

    case_tags: list[set[str]] | None
    sample_tags: list[set[str]]
