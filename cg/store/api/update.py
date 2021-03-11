"""Module to updating existing records in status-db tables"""

import datetime as dt
from cg.store import Store, models
from typing import Optional


def update_analysis_uploaded_to_vogue_date(
    status_api: Store,
    analysis_obj: models.Analysis,
    vogue_upload_date: Optional[dt.datetime] = dt.datetime.now(),
) -> models.Analysis:
    """ updates the uploaded to vogue date for an analysis"""
    analysis_obj.uploaded_to_vogue_at = vogue_upload_date
    status_api.commit()
    return analysis_obj
