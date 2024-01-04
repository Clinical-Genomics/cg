class ReadInformation:
    def __init__(
        self, flow_cell_name: str, reads_per_lane: list[dict], reads_mapped_per_lane: list[dict]
    ):
        reads_per_lane: dict
        reads_mapped_per_lane: dict
        percentage_mapped_per_lane: dict
        total_reads: int
        average_percentage_mapped: float
        flow_cell_name: str
