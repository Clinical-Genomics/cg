from pydantic import BaseModel


class CreateJobRequest(BaseModel):
    slurm_id: str
    job_type: str
