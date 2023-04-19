import http
import os
import tempfile
from datetime import date
from cg.constants.invoice import CostCenters
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
    abort,
)
from flask_dance.contrib.google import google

from cg.apps.invoice.render import render_xlsx
from cg.meta.invoice import InvoiceAPI
from cg.server.ext import db, lims
from typing import List, Union
from cg.store.models import Customer, Invoice, Pool, Sample


BLUEPRINT = Blueprint("invoices", __name__, template_folder="templates")


@BLUEPRINT.before_request
def before_request():
    if not logged_in():
        return redirect(url_for("admin.index"))


def logged_in():
    user = db.get_user_by_email(email=session.get("user_email"))
    return google.authorized and user and user.is_admin


def undo_invoice(invoice_id):
    invoice_obj: Invoice = db.get_invoice_by_entry_id(entry_id=invoice_id)
    record_type: str = invoice_obj.record_type
    records: List[Union[Pool, Sample]] = db.get_pools_and_samples_for_invoice_by_invoice_id(
        invoice_id=invoice_id
    )
    db.session.delete(invoice_obj)
    for record in records:
        record.invoice_id = None
    db.session.commit()

    return url_for(".new", record_type=record_type)


def make_new_invoice():
    customer_id = request.form.get("customer")
    customer: Customer = db.get_customer_by_internal_id(customer_internal_id=customer_id)
    record_ids = request.form.getlist("records")
    record_type = request.form.get("record_type")
    if len(record_ids) == 0:
        return redirect(url_for(".new", record_type=record_type))
    if record_type == "Pool":
        pools: List[Pool] = [db.get_pool_by_entry_id(pool_id) for pool_id in record_ids]
        new_invoice: Invoice = db.add_invoice(
            customer=customer,
            pools=pools,
            comment=request.form.get("comment"),
            discount=int(request.form.get("discount", "0")),
            record_type="Pool",
        )
    elif record_type == "Sample":
        samples: List[Sample] = [
            db.get_sample_by_internal_id(sample_id) for sample_id in record_ids
        ]
        new_invoice: Invoice = db.add_invoice(
            customer=customer,
            samples=samples,
            comment=request.form.get("comment"),
            discount=int(request.form.get("discount", "0")),
            record_type="Sample",
        )

    db.session.add(new_invoice)
    db.session.commit()
    return url_for(".invoice", invoice_id=new_invoice.id)


def upload_invoice_news_to_db():
    invoice_id: int = request.form.get("invoice_id")
    invoice_obj: Invoice = db.get_invoice_by_entry_id(entry_id=invoice_id)
    invoice_obj.comment = request.form.get("comment")

    if request.form.get("final_price") != invoice_obj.price:
        invoice_obj.price = request.form.get("final_price")

    if request.form.get("invoice_sent") and not invoice_obj.invoiced_at:
        invoice_obj.invoiced_at = date.today()
    elif not request.form.get("invoice_sent"):
        invoice_obj.invoiced_at = None

    kth_excel_file = request.files.get("KTH_excel")
    if kth_excel_file:
        invoice_obj.excel_kth = kth_excel_file.stream.read()
    ki_excel_file = request.files.get("KI_excel")
    if ki_excel_file:
        invoice_obj.excel_ki = ki_excel_file.stream.read()
    db.session.commit()
    return url_for("invoices.invoice", invoice_id=invoice_id)


@BLUEPRINT.route("/")
def index():
    """Retrieve invoices."""
    invoices = {
        "sent_invoices": db.get_invoices_by_status(is_invoiced=True),
        "pending_invoices": db.get_invoices_by_status(is_invoiced=False),
    }
    return render_template("invoices/index.html", invoices=invoices)


@BLUEPRINT.route("/", methods=["POST"])
def update_invoices():
    """Update invoices."""
    if request.form.get("new_invoice_updates"):
        url = upload_invoice_news_to_db()
        return redirect(url)
    elif request.form.get("undo"):
        invoice_id = request.form.get("invoice_id")
        url = undo_invoice(invoice_id)
        return redirect(url)
    else:
        url = make_new_invoice()
        return redirect(url)


@BLUEPRINT.route("/new/<record_type>")
def new(record_type):
    """Generate a new invoice."""
    count = request.args.get("total", 0)
    customer_id = request.args.get("customer", "cust002")
    customer: Customer = db.get_customer_by_internal_id(customer_internal_id=customer_id)
    if record_type == "Sample":
        records: List[Union[Pool, Sample]] = db.get_samples_to_invoice_for_customer(
            customer=customer
        )
        customers_to_invoice: List[Customer] = db.get_customers_to_invoice(
            records=db.get_samples_to_invoice_query()
        )
    elif record_type == "Pool":
        records: List[Union[Pool, Sample]] = db.get_pools_to_invoice_for_customer(customer=customer)
        customers_to_invoice: List[Customer] = db.get_customers_to_invoice(
            records=db.get_pools_to_invoice_query()
        )
    return render_template(
        "invoices/new.html",
        customers_to_invoice=customers_to_invoice,
        count=count,
        records=records,
        record_type=record_type,
        total_price_threshold=current_app.config["TOTAL_PRICE_THRESHOLD"],
        args={"customer": customer_id},
    )


@BLUEPRINT.route("/<int:invoice_id>", methods=["GET"])
def invoice(invoice_id):
    """Save comments and uploaded modified invoices."""
    invoice_obj: Invoice = db.get_invoice_by_entry_id(entry_id=invoice_id)
    api = InvoiceAPI(db, lims, invoice_obj)
    kth_inv = api.get_invoice_report(CostCenters.kth)
    ki_inv = api.get_invoice_report(CostCenters.kth)

    if not (kth_inv and ki_inv):
        flash(" ,".join(list(set(api.log))))
        undo_invoice(invoice_id)
        return redirect(request.referrer)

    if not invoice_obj.price:
        final_price = api.total_price()
    else:
        final_price = invoice_obj.price

    return render_template(
        "invoices/invoice.html",
        invoice=invoice_obj,
        invoice_dict={"KTH": kth_inv, "KI": ki_inv},
        default_price=api.total_price(),
        final_price=final_price,
        record_type=invoice_obj.record_type,
    )


@BLUEPRINT.route("/<int:invoice_id>/excel")
def invoice_template(invoice_id):
    """Generate invoice template"""
    cost_center = request.args.get("cost_center", "KTH")
    invoice_obj: Invoice = db.get_invoice_by_entry_id(entry_id=invoice_id)
    api = InvoiceAPI(db, lims, invoice_obj)
    invoice_dict = api.get_invoice_report(cost_center)
    workbook = render_xlsx(invoice_dict)

    temp_dir = tempfile.gettempdir()
    filename = "Invoice_{}_{}.xlsx".format(invoice_obj.id, cost_center)
    excel_path = os.path.join(temp_dir, filename)
    workbook.save(excel_path)

    return send_from_directory(directory=temp_dir, filename=filename, as_attachment=True)


@BLUEPRINT.route("/<int:invoice_id>/invoice_file/<cost_center>")
def modified_invoice(invoice_id, cost_center):
    """Enables download of modified invoices saved in the database."""
    if cost_center not in ["KTH", "KI"]:
        return abort(http.HTTPStatus.BAD_REQUEST)

    invoice_obj: Invoice = db.get_invoice_by_entry_id(entry_id=invoice_id)
    file_name = "invoice_" + cost_center + str(invoice_id) + ".xlsx"
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, file_name)
    with open(file_path, "wb") as file_object:
        if cost_center == "KTH":
            file_object.write(invoice_obj.excel_kth)
        elif cost_center == "KI":
            file_object.write(invoice_obj.excel_ki)
    return send_from_directory(directory=temp_dir, filename=file_name, as_attachment=True)
