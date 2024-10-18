from cg.services.deliver_files.file_fetcher.models import DeliveryFiles
from cg.services.deliver_files.file_filter.abstract import FilterDeliveryFilesService


class SampleFileFilter(FilterDeliveryFilesService):

    def filter_delivery_files(self, delivery_files: DeliveryFiles, sample_id: str) -> DeliveryFiles:
        for index in range(len(delivery_files.sample_files)):
            if delivery_files.sample_files[index].sample_id != sample_id:
                delivery_files.sample_files.pop(index)
        return delivery_files
