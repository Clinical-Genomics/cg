"""Module to updating existing records in status-db tables"""

import datetime as dt
from typing import Optional

from cg.store import models


def update_analysis_uploaded_to_vogue_date(
    case: models.Family,
    vogue_upload_date: Optional[dt.datetime] = dt.datetime.now(),
) -> models.Family:
    """ updates the uploaded to vogue date for the most recent analysis of a given case"""
    analysis_obj = case.analyses[0]
    analysis_obj.uploaded_to_vogue_at = vogue_upload_date
    return case
