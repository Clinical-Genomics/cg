from pydantic import BaseModel, Field


class ReadMetric(BaseModel):
    """Metrics for a read for a sample on a tile in a lane."""

    read_yield: int = Field(..., alias="Yield", ge=0)
    read_yield_q30: int = Field(..., alias="YieldQ30", ge=0)
    read_quality_score_sum: int = Field(..., alias="QualityScoreSum", ge=0)


class TileReads(BaseModel):
    """Metrics for a sample on a tile in a lane."""

    sample_id: str = Field(..., alias="SampleId", min_length=1)
    tile_sample_reads: int = Field(..., alias="NumberReads", ge=0)
    tile_sample_yield: int = Field(..., alias="Yield", ge=0)
    tile_sample_read_metrics: list[ReadMetric] = Field(..., alias="ReadMetrics")


class UndeterminedTileReads(BaseModel):
    """Metrics for reads without a sample id within a tile of a lane."""

    tile_total_reads: int = Field(..., alias="NumberReads", ge=0)
    tile_total_yield: int = Field(..., alias="Yield", ge=0)
    tile_read_metrics: list[ReadMetric] = Field(..., alias="ReadMetrics")


class ConversionResult(BaseModel):
    """Demultiplexing results and undetermined reads for a tile within a lane."""

    lane: int = Field(..., alias="LaneNumber", gt=0)
    tile_reads: list[TileReads] = Field(..., alias="DemuxResults")
    tile_undetermined_reads: UndeterminedTileReads | None = Field(None, alias="Undetermined")


class SampleLaneTileMetrics(BaseModel):
    """Metrics for samples on a tile in a lane on a flow cell from a bcl2fastq run."""

    flow_cell_name: str = Field(..., alias="Flowcell", min_length=1)
    conversion_results: list[ConversionResult] = Field(..., alias="ConversionResults")


class SampleLaneMetrics(BaseModel):
    """Metrics for a sample in a lane from a bcl2fastq run."""

    flow_cell_name: str
    lane: int
    sample_id: str
    total_reads: int
    total_yield: int
    total_yield_q30: int
    total_quality_score: int
