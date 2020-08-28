# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots["test_parse_config 1"] = {
    "case": "case_id",
    "email": None,
    "is_dryrun": False,
    "out_dir": "tests/fixtures/apps/mip/rna/store/",
    "priority": "low",
    "sampleinfo_path": "tests/fixtures/apps/mip/rna/store/case_qc_sample_info.yaml",
    "samples": [{"id": "sample_id", "type": "wts"}],
}

snapshots["test_parse_sampleinfo_data 1"] = {
    "case": "case_id",
    "date": GenericRepr("datetime.datetime(2019, 11, 21, 14, 31, 2)"),
    "is_finished": True,
    "version": "v7.1.4",
}
