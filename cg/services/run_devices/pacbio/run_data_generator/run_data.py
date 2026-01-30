from pathlib import Path

from cg.services.run_devices.abstract_models import RunData


class PacBioRunData(RunData):
    """Holds information on a single SMRTcell of a PacBio run."""

    full_path: Path
    run_id: str
    well_name: str
    plate: int
