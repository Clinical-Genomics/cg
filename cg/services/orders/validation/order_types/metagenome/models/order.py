from cg.services.orders.validation.models.order_with_samples import OrderWithSamples
from cg.services.orders.validation.order_types.metagenome.constants import MetagenomeDeliveryType
from cg.services.orders.validation.order_types.metagenome.models.sample import MetagenomeSample


class MetagenomeOrder(OrderWithSamples[MetagenomeSample]):
    delivery_type: MetagenomeDeliveryType
