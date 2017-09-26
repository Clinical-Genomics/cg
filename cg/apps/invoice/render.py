# -*- coding: utf-8 -*-
import datetime as dt
from pkg_resources import resource_filename

from openpyxl import load_workbook, Workbook
from openpyxl.styles import Border, Font, PatternFill, Side


def render_xlsx(data: dict) -> Workbook:
    """Render an Excel invoice template.

    Data is intended to look as follows:

        {
            'invoice_id': str,
            'costcenter': str,
            'project_number': str,
            'customer_id': str,
            'customer_name': str,
            'agreement': str,
            'contact': {
                'name': str,
                'email': str,
                'reference': str,
                'customer_name': str,
                'address': str
            },
            'samples': [{
                'name': str,
                'lims_id': str,
                'application_tag': str,
                'project': str,
                'date': str,
                'price': int
            }]
        }
    """
    pkg_dir = __name__.rpartition('.')[0]
    template_path = resource_filename(pkg_dir, 'templates/invoice.xlsx')
    workbook = load_workbook(template_path)
    worksheet = workbook.active
    worksheet['C1'] = data['costcenter'].upper()
    worksheet['F1'] = f"{data['invoice_id']}-{data['costcenter']}"
    worksheet['F2'] = dt.datetime.today().date()
    worksheet['C7'] = data['project_number']
    worksheet['C13'] = data['contact']['name']
    worksheet['C14'] = data['contact']['email']
    worksheet['C15'] = data['contact']['reference']
    worksheet['C16'] = data['contact']['customer_name']
    worksheet['C17'] = data['contact']['address']
    worksheet['C20'] = f"{data['customer_id']} / {data['customer_name']}"

    if data.get('agreement'):
        worksheet['A21'] = 'Avtaltets diarienummer'
        worksheet['C21'] = data['agreement']

    samples_start = 24
    for index, sample_data in enumerate(data['samples']):
        row = samples_start + index
        worksheet[f"A{row}"] = sample_data['name']
        worksheet[f"B{row}"] = sample_data['lims_id']
        worksheet[f"C{row}"] = sample_data['application_tag']
        worksheet[f"D{row}"] = sample_data['project']
        worksheet[f"E{row}"] = sample_data['date']
        worksheet[f"F{row}"] = sample_data['price']

    worksheet[f"E{row + 2}"] = 'Total'
    worksheet[f"F{row + 2}"] = f"=SUM(F{samples_start}: F{row})"

    header_rows = [5, 12, 19, 23, row + 2]
    for header_row in header_rows:
        for column in ['A', 'B', 'C', 'D', 'E', 'F']:
            cell = worksheet[f"{column}{header_row}"]
            cell.font = Font(bold=True)
            cell.border = Border(top=Side(border_style='thin', color='000000'),
                                 bottom=Side(border_style='thin', color='000000'))
            cell.fill = PatternFill('solid', fgColor='E5E8E8')

    return workbook
