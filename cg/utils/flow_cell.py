def get_flow_cell_id(flow_cell_dir_name: str) -> str:
    """Return the flow cell id from the flow cell directory name.
    Example: 230802_A00689_0857_BHGTMFDSX7 -> HGTMFDSX7
    """
    return flow_cell_dir_name.split("_")[-1][1:]
