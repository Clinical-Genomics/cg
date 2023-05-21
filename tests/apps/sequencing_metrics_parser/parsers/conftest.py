import pytest


@pytest.fixture
def valid_bcl2fastq_metrics_data():
    return {
        "Flowcell": "AB1",
        "RunNumber": 1,
        "RunId": "RUN1",
        "ReadInfosForLanes": [
            {
                "LaneNumber": 1,
            }
        ],
        "ConversionResults": [
            {
                "LaneNumber": 1,
                "TotalClustersRaw": 100,
                "TotalClustersPF": 100,
                "Yield": 1000,
                "DemuxResults": [
                    {
                        "SampleId": "S1",
                        "SampleName": "Sample1",
                        "IndexMetrics": [{"IndexSequence": "ATGC", "MismatchCounts": {"ATGC": 1}}],
                        "NumberReads": 1,
                        "Yield": 100,
                        "ReadMetrics": [
                            {"ReadNumber": 1, "Yield": 100, "YieldQ30": 90, "QualityScoreSum": 100}
                        ],
                    }
                ],
            }
        ],
    }
