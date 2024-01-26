from pydantic import BaseModel

from cg.constants.constants import JobType


class CreateJobRequest(BaseModel):
    slurm_id: str
    job_type: JobType
