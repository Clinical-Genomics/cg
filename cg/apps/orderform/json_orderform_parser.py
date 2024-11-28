from cg.apps.orderform.orderform_parser import OrderformParser
from cg.constants import DataDelivery, Workflow
from cg.exc import OrderFormError
from cg.models.orders.json_sample import JsonSample
from cg.models.orders.order import OrderType


class JsonOrderformParser(OrderformParser):
    ACCEPTED_DATA_ANALYSES: list[str] = [
        Workflow.MIP_DNA,
        Workflow.MIP_RNA,
        Workflow.FLUFFY,
        Workflow.BALSAMIC,
    ]
    NO_VALUE: str = "no_value"
    samples: list[JsonSample] = []

    def get_project_type(self) -> str:
        """Determine the project type."""

        data_analyses: set[str] = {sample.data_analysis.lower() for sample in self.samples}

        if len(data_analyses) > 1:
            raise OrderFormError(f"mixed 'Data Analysis' types: {', '.join(data_analyses)}")

        data_analysis: str = data_analyses.pop()
        if data_analysis in self.ACCEPTED_DATA_ANALYSES:
            return data_analysis

        raise OrderFormError(f"Unsupported data_analysis: {data_analyses} for json data")

    @staticmethod
    def project_type_to_order_type(project_type: str) -> str:
        """In the case where data delivery was not defined we map from project type"""
        project_to_order = {
            OrderType.METAGENOME: DataDelivery.FASTQ,
            OrderType.FASTQ: DataDelivery.FASTQ,
            OrderType.RML: DataDelivery.FASTQ,
            OrderType.MIP_RNA: DataDelivery.ANALYSIS_FILES,
            OrderType.FLUFFY: DataDelivery.STATINA,
        }
        if project_type not in project_to_order:
            raise OrderFormError(f"Could not find data delivery for: {project_type}")
        return project_to_order[project_type]

    def get_data_delivery(self) -> str:
        """Determine the order_data delivery type."""

        data_deliveries = {sample.data_delivery for sample in self.samples}

        if len(data_deliveries) > 1:
            raise OrderFormError(f"mixed 'Data Delivery' types: {', '.join(data_deliveries)}")

        data_delivery = data_deliveries.pop()

        if data_delivery == self.NO_VALUE:
            return str(self.project_type_to_order_type(self.project_type))

        if data_delivery == str(DataDelivery.NIPT_VIEWER):
            return str(DataDelivery.STATINA)

        try:
            return str(DataDelivery(data_delivery))
        except ValueError:
            raise OrderFormError(f"Unsupported order_data delivery: {data_delivery}")

    def parse_orderform(self, order_data: dict) -> None:
        """Parse order form in JSON format."""

        self.samples: list[JsonSample] = [
            JsonSample.model_validate(sample_data) for sample_data in order_data.get("samples", [])
        ]
        if not self.samples:
            raise OrderFormError("orderform doesn't contain any samples")

        self.project_type = self.get_project_type()
        self.delivery_type = self.get_data_delivery()
        self.customer_id = order_data["customer"].lower()
        self.order_comment = order_data.get("comment")
        self.order_name = order_data.get("name")
