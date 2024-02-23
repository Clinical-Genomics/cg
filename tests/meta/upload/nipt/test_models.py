import math

import pytest
from pydantic import ValidationError

from cg.meta.upload.nipt.models import FlowCellQ30AndReads, StatinaUploadFiles


def test_statina_upload_files_required_field():
    with pytest.raises(ValidationError):
        StatinaUploadFiles()


def test_statina_upload_files_init():
    upload_files = StatinaUploadFiles(result_file="result.txt")
    assert upload_files.result_file == "result.txt"
    assert upload_files.multiqc_report is None
    assert upload_files.segmental_calls is None


def test_statina_upload_files_optional_fields():
    upload_files = StatinaUploadFiles(
        result_file="result.txt",
        multiqc_report="multiqc.html",
        segmental_calls="segmental_calls.txt",
    )
    assert upload_files.result_file == "result.txt"
    assert upload_files.multiqc_report == "multiqc.html"
    assert upload_files.segmental_calls == "segmental_calls.txt"


def test_flow_cell_q30_and_reads_init():
    flow_cell = FlowCellQ30AndReads(total_reads_on_flow_cell=5000, average_q30_across_samples=90.5)
    assert flow_cell.total_reads_on_flow_cell == 5000
    assert math.isclose(flow_cell.average_q30_across_samples, 90.5, rel_tol=1e-9)


def test_passes_read_threshold():
    flow_cell = FlowCellQ30AndReads(total_reads_on_flow_cell=5000, average_q30_across_samples=90.5)
    assert flow_cell.passes_read_threshold(4000) is True
    assert flow_cell.passes_read_threshold(6000) is False


def test_passes_q30_threshold():
    flow_cell = FlowCellQ30AndReads(total_reads_on_flow_cell=5000, average_q30_across_samples=90.5)
    assert flow_cell.passes_q30_threshold(80.0) is True
    assert flow_cell.passes_q30_threshold(95.0) is False
