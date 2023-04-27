from typing import Dict, List, Optional

from pydantic import BaseModel


class MultiqcDataJson(BaseModel):
    """Multiqc data json model."""

    report_general_stats_data: Optional[List[Dict]]
    report_data_sources: Optional[Dict]
