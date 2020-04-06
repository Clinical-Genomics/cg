"""Add common rutines for analysis workflows"""

from cg.apps.lims import LimsAPI
from cg.exc import CgDataError, LimsDataError
from cg.store import Store


def get_target_bed_from_lims(lims: LimsAPI, status_db: Store, target_bed):
    """Get target bed filename from lims"""
    target_bed_shortname = lims.capture_kit(target_bed)
    if not target_bed_shortname:
        raise LimsDataError("Target bed %s not found in LIMS" % target_bed_shortname)
    bed_version_obj = status_db.bed_version(target_bed_shortname)
    if not bed_version_obj:
        raise CgDataError("Bed-version %s does not exist" % target_bed_shortname)
    return bed_version_obj.filename
