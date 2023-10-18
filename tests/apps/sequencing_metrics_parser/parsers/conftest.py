import json
from pathlib import Path

import pytest

from cg.constants.demultiplexing import (
    BCL2FASTQ_METRICS_DIRECTORY_NAME,
    BCL2FASTQ_METRICS_FILE_NAME,
)


@pytest.fixture
def raw_bcl2fastq_tile_metrics() -> dict:
    """Metrics for a single tile in a lane."""
    return {
        "Flowcell": "AB1",
        "RunNumber": 1,
        "RunId": "RUN1",
        "ConversionResults": [
            {
                "LaneNumber": 1,
                "DemuxResults": [
                    {
                        "SampleId": "S1",
                        "NumberReads": 1,
                        "Yield": 100,
                        "ReadMetrics": [{"Yield": 100, "YieldQ30": 90, "QualityScoreSum": 100}],
                    }
                ],
                "Undetermined": {
                    "NumberReads": 1,
                    "Yield": 100,
                    "ReadMetrics": [
                        {
                            "ReadNumber": 1,
                            "Yield": 100,
                            "YieldQ30": 80,
                            "QualityScoreSum": 3000,
                            "TrimmedBases": 0,
                        }
                    ],
                },
            }
        ],
    }


@pytest.fixture
def bcl2fastq_flow_cell_path(
    tmp_path: Path,
    raw_bcl2fastq_tile_metrics: dict,
) -> Path:
    """Flow cell with one sample in one lane, two tiles, two paired reads and two undetermined paired reads."""

    tile_1 = Path(tmp_path, "l1t1", BCL2FASTQ_METRICS_DIRECTORY_NAME)
    tile_1.mkdir(parents=True)
    tile_1_stats_json_path = Path(tile_1, BCL2FASTQ_METRICS_FILE_NAME)

    tile_2 = Path(tmp_path, "l1t2", BCL2FASTQ_METRICS_DIRECTORY_NAME)
    tile_2.mkdir(parents=True)
    tile_2_stats_json_path = Path(tile_2, BCL2FASTQ_METRICS_FILE_NAME)

    tile_1_stats_json_path.write_text(json.dumps(raw_bcl2fastq_tile_metrics))
    tile_2_stats_json_path.write_text(json.dumps(raw_bcl2fastq_tile_metrics))

    return tmp_path
