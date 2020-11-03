"""Test MIP RNA files"""

from snapshottest import Snapshot

from cg.apps.mip import parse_sampleinfo


def test_parse_sampleinfo_rna_result_contents(snapshot: Snapshot, files_raw: dict):
    """test parse_sampleinfo_rna using snapshot

    Note: to retake all snapshots run `pytest --snapshot-update`

    Args:
        snapshot (Snapshot): a file with a snapshot of the correct test result, see
        cg/cg/tests/snapshots/snap_test_apps_mip_files.py
        files_raw (dict): dict of raw .yaml files
    """
    # GIVEN an RNA sample info file
    sampleinfo_raw = files_raw["rna_sampleinfo"]

    # WHEN parsing the file
    sampleinfo_data = parse_sampleinfo.parse_sampleinfo_rna(sampleinfo_raw)

    # THEN the result should contains the data as specified by the MIP team
    snapshot.assert_match(sampleinfo_data)
