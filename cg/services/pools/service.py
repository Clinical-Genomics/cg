from cg.server.dto.pools.requests import PoolsRequest
from cg.store.store import Store


class PoolsService:

    def __init__(self, store: Store):
        self.store = store

    def get_pools(self, request: PoolsRequest) -> tuple[list[dict], int]:
        """Get pools based on the provided filters."""
        pools, total = self.store.get_pools_to_render(
            enquiry=request.enquiry,
            limit=request.page_size,
            offset=(request.page - 1) * request.page_size,
        )
        parsed_pools: list[dict] = [pools.to_dict() for pools in pools]
        return parsed_pools, total
