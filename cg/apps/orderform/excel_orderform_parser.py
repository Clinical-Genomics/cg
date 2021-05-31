import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import openpyxl
from openpyxl.cell.cell import Cell
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from pydantic import parse_obj_as

from cg.apps.orderform.orderform_parser import OrderformParser
from cg.constants import DataDelivery
from cg.exc import OrderFormError
from cg.meta.orders import OrderType
from cg.models.orders.excel_sample import ExcelSample

LOG = logging.getLogger(__name__)


class ExcelOrderformParser(OrderformParser):
    NO_ANALYSIS: str = "no-analysis"
    NO_VALUE: str = "no_value"
    SHEET_NAMES: List[str] = ["Orderform", "orderform", "order form"]
    VALID_ORDERFORMS: List[str] = [
        "1508:24",  # Orderform MIP, Balsamic, sequencing only, MIP RNA
        "1541:6",  # Orderform Externally sequenced samples
        "1603:10",  # Microbial WGS
        "1604:10",  # Orderform Ready made libraries (RML)
        "1605:9",  # Microbial meta genomes
        "2184:5",  # Orderform SARS-CoV-2
    ]

    def check_orderform_version(self, document_title: str) -> None:
        """Raise an error if the orderform is too new or too old for the order portal."""
        LOG.info("Validating that %s is a correct orderform version", document_title)
        for valid_orderform in self.VALID_ORDERFORMS:
            if valid_orderform in document_title:
                return
        raise OrderFormError(f"Unsupported orderform: {document_title}")

    def get_sheet_name(self, sheet_names: List[str]) -> str:
        """Return the correct (existing) sheet names"""

        for name in sheet_names:
            if name in self.SHEET_NAMES:
                LOG.info("Found sheet name %s", name)
                return name
        raise OrderFormError("'orderform' sheet not found in Excel file")

    @staticmethod
    def get_document_title(workbook: Workbook, orderform_sheet: Worksheet) -> str:
        """Get the document title for the order form.

        Openpyxl use 1 based counting
        """
        for sheet_number, sheet_name in enumerate(workbook.sheetnames):
            if sheet_name.lower() != "information":
                continue
            information_sheet: Worksheet = workbook[sheet_name]
            document_title = information_sheet.cell(1, 3).value
            LOG.info("Found document title %s", document_title)
            return document_title

        document_title = orderform_sheet.cell(1, 2).value
        LOG.info("Found document title %s", document_title)
        return document_title

    @staticmethod
    def get_sample_row_info(
        row: Tuple[Cell], header_row: List[str], empty_row_found: bool
    ) -> Optional[dict]:
        """Convert an excel row with sample data into a dict with sample info"""
        values = []
        cell: Cell
        for cell in row:
            value = str(cell.value)
            if value == "None":
                value = ""
            if value == "NA":
                value = None
            values.append(value)

        if not values[0]:
            return None
        # skip empty rows
        if empty_row_found:
            raise OrderFormError(
                f"Found data after empty lines. Please delete any "
                f"non-sample data rows in between the samples"
            )

        sample_dict = dict(zip(header_row, values))
        sample_dict.pop(None)
        return sample_dict

    @staticmethod
    def get_header(rows: List[Tuple[Cell]]) -> List[str]:
        header_row: List[str] = []
        header = False
        for row in rows:
            if header:
                return [cell.value for cell in row]
            if row[0].value == "<TABLE HEADER>":
                LOG.debug("Found header row")
                header = True
        return header_row

    @staticmethod
    def get_raw_samples(rows: List[Tuple[Cell]], header_row: List[str]) -> List[dict]:
        raw_samples: List[dict] = []
        sample_rows = False
        empty_row_found = False
        for row in rows:
            if row[0].value == "</SAMPLE ENTRIES>":
                LOG.debug("End of samples info")
                return raw_samples

            if sample_rows:
                sample_dict: Optional[dict] = ExcelOrderformParser.get_sample_row_info(
                    row=row, header_row=header_row, empty_row_found=empty_row_found
                )
                if sample_dict:
                    raw_samples.append(sample_dict)
                else:
                    empty_row_found = True

            elif row[0].value == "<SAMPLE ENTRIES>":
                LOG.debug("Found samples row")
                sample_rows = True
        return raw_samples

    @staticmethod
    def relevant_rows(orderform_sheet: Worksheet) -> List[Dict[str, str]]:
        """Get the relevant rows from an order form sheet."""
        # orderform_sheet.rows is a generator. Convert to list to be able to iterate multiple times
        rows = list(orderform_sheet.rows)
        header_row: List[str] = ExcelOrderformParser.get_header(rows)
        return ExcelOrderformParser.get_raw_samples(rows=rows, header_row=header_row)

    def get_project_type_from_samples(self) -> str:
        analyses = {sample.data_analysis for sample in self.samples}

        if len(analyses) != 1:
            raise OrderFormError(f"mixed 'Data Analysis' types: {', '.join(analyses)}")

        analysis = analyses.pop().lower().replace(" ", "-")
        return "fastq" if analysis == self.NO_ANALYSIS else analysis

    def get_project_type(self, document_title: str) -> str:
        """Determine the project type and set it to the class."""
        document_number_to_project_type = {
            "1541": str(OrderType.EXTERNAL),
            "1604": str(OrderType.RML),
            "1603": str(OrderType.MICROSALT),
            "1605": str(OrderType.METAGENOME),
            "2184": str(OrderType.SARS_COV_2),
        }
        for document_number, value in document_number_to_project_type.items():
            if document_number in document_title:
                return value

        if "1508" in document_title:
            return self.get_project_type_from_samples()

        raise OrderFormError(f"Undetermined project type in: {document_title}")

    def parse_data_analysis(self) -> str:
        data_analyses = {sample.data_analysis for sample in self.samples if sample.data_analysis}

        if len(data_analyses) > 1:
            raise OrderFormError(f"mixed 'Data Analysis' types: {', '.join(data_analyses)}")

        return data_analyses.pop().lower().replace(" ", "-")

    def is_from_orderform_without_data_delivery(self, data_delivery: str) -> bool:
        return data_delivery == self.NO_VALUE

    def default_delivery_type(self, project_type: OrderType) -> str:
        """Returns the default delivery type for a project type"""
        if project_type == OrderType.FLUFFY:
            return DataDelivery.NIPT_VIEWER

        if project_type == OrderType.METAGENOME:
            return DataDelivery.FASTQ

        if project_type == OrderType.MICROSALT:
            data_analysis: str = self.parse_data_analysis()

            if data_analysis == "custom":
                return DataDelivery.FASTQ_QC

            if data_analysis == "fastq":
                return DataDelivery.FASTQ

        if project_type == OrderType.RML:
            return DataDelivery.FASTQ

        if project_type == OrderType.EXTERNAL:
            return DataDelivery.SCOUT

        raise OrderFormError(f"Could not determine value for Data Delivery")

    def get_data_delivery(self, project_type: OrderType) -> str:
        """Determine the order_data delivery type."""

        data_delivery: str = self.parse_data_delivery()

        if self.is_from_orderform_without_data_delivery(data_delivery):
            return self.default_delivery_type(project_type)

        if data_delivery == "analysis-+-bam":
            return DataDelivery.ANALYSIS_BAM_FILES
        if data_delivery == "fastq-qc":
            return DataDelivery.FASTQ_QC

        try:
            return DataDelivery(data_delivery)
        except ValueError:
            raise OrderFormError(f"Unsupported Data Delivery: {data_delivery}")

    def parse_data_delivery(self) -> str:

        data_deliveries = {sample.data_delivery or self.NO_VALUE for sample in self.samples}

        if len(data_deliveries) > 1:
            raise OrderFormError(f"mixed 'Data Delivery' types: {', '.join(data_deliveries)}")

        return data_deliveries.pop().lower().replace(" ", "-")

    def get_customer_id(self) -> str:
        """Set the customer id"""

        customers = {sample.customer for sample in self.samples}
        if len(customers) != 1:
            raise OrderFormError("Invalid customer information: {}".format(customers))
        return customers.pop()

    def parse_orderform(self, excel_path: str) -> None:
        """Parse out information from an order form."""

        LOG.info("Open excel workbook from file %s", excel_path)
        workbook: Workbook = openpyxl.load_workbook(
            filename=excel_path, read_only=True, data_only=True
        )

        sheet_name: str = self.get_sheet_name(workbook.sheetnames)

        orderform_sheet: Worksheet = workbook[sheet_name]
        document_title: str = self.get_document_title(
            workbook=workbook, orderform_sheet=orderform_sheet
        )
        self.check_orderform_version(document_title)

        LOG.info("Parsing all samples from orderform")
        raw_samples: List[dict] = self.relevant_rows(orderform_sheet)

        if not raw_samples:
            raise OrderFormError("orderform doesn't contain any samples")

        self.samples: List[ExcelSample] = parse_obj_as(List[ExcelSample], raw_samples)
        self.project_type: str = self.get_project_type(document_title)
        self.delivery_type = self.get_data_delivery(project_type=OrderType(self.project_type))
        self.customer_id = self.get_customer_id()

        self.order_name = Path(excel_path).stem
