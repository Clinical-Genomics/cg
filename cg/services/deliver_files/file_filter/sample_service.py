from cg.services.deliver_files.file_fetcher.models import DeliveryFiles
from cg.services.deliver_files.file_filter.abstract import FilterDeliveryFilesService


class SampleFileFilter(FilterDeliveryFilesService):

    def filter_delivery_files(self, delivery_files: DeliveryFiles, sample_id: str) -> DeliveryFiles:
        delivery_files.sample_files = [
            sample_file
            for sample_file in delivery_files.sample_files
            if sample_file.sample_id == sample_id
        ]
        return delivery_files
