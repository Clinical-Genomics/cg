from flask import Blueprint, render_template, request, redirect, url_for

from cg.server.ext import db

BLUEPRINT = Blueprint('invoices', __name__, template_folder='templates')

@BLUEPRINT.route('/', methods=['GET', 'POST'])
def index():
    """Show invoices."""
    if request.method == 'POST':
        customer_id = request.form.get('customer')
        customer_obj = db.customer(customer_id)
        sample_ids = request.form.getlist('samples')
        if len(sample_ids) == 0:
            return redirect(url_for('.new'))
        samples = [db.sample(sample_id) for sample_id in sample_ids]
        new_invoice = db.add_invoice(
            customer=customer_obj,
            samples=samples,
            comment=request.form.get('comment'),
            discount=int(request.form.get('discount', '0')),
        )
        db.add_commit(new_invoice)
        return redirect(url_for('.invoice', invoice_id=new_invoice.id))

    invoices = db.invoices()
    return render_template('invoices/index.html', invoices=invoices)


@BLUEPRINT.route('/<int:invoice_id>')
def invoice(invoice_id):
    """Show an invoice."""
    invoice_obj = db.invoice(invoice_id)
    return render_template('invoices/invoice.html', invoice=invoice_obj)


@BLUEPRINT.route('/new')
def new():
    """Generate a new invoice."""
    customers = db.customers()
    customer_id = request.args.get('customer', 'cust002')
    customer_obj = db.customer(customer_id)
    samples = db.samples_to_invoice(customer=customer_obj).limit(50)
    return render_template(
        'invoices/new.html',
        customers=customers,
        samples=samples,
        args={
            'customer': customer_id,
        }
    )
