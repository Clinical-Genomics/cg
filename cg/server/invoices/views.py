from flask import Blueprint, render_template, request, redirect, url_for, send_from_directory
from cg.meta.invoice import InvoiceAPI
import tempfile
import os
from cg.server.ext import db, lims
from cg.apps.invoice.render import render_xlsx
from datetime import date


BLUEPRINT = Blueprint('invoices', __name__, template_folder='templates')

@BLUEPRINT.route('/', methods=['GET', 'POST'])
def index():
    """Show invoices."""
    if request.method == 'POST':
        customer_id = request.form.get('customer')
        customer_obj = db.customer(customer_id)
        record_ids = request.form.getlist('records')
        record_type = request.form.get('record_type')
        
        if len(record_ids) == 0:
            return redirect(url_for('.new', record_type=record_type))
        if record_type=='Pool':
            pools = [db.pool(pool_id) for pool_id in record_ids]
            new_invoice = db.add_invoice(
                customer=customer_obj,
                pools=pools,
                comment=request.form.get('comment'),
                discount=int(request.form.get('discount', '0')))      
        elif record_type=='Sample':
            samples = [db.sample(sample_id) for sample_id in record_ids]
            new_invoice = db.add_invoice(
                customer=customer_obj,
                samples=samples,
                comment=request.form.get('comment'),
                discount=int(request.form.get('discount', '0')))
        db.add_commit(new_invoice)
        return redirect(url_for('.invoice', invoice_id=new_invoice.id))

    invoices = {'sent_invoices' : db.invoices(invoiced=True),
                'pending_invoices' : db.invoices(invoiced=False)}

    return render_template('invoices/index.html', invoices=invoices)


@BLUEPRINT.route('/new/<record_type>')
def new(record_type):
    """Generate a new invoice."""
    customers = db.customers()
    customer_id = request.args.get('customer', 'cust002')
    customer_obj = db.customer(customer_id)
    
    if record_type=='Sample':
        records = db.samples_to_invoice(customer=customer_obj).limit(50)
    elif record_type=='Pool':
        records = db.pools_to_invoice(customer=customer_obj).limit(50)


    return render_template(
        'invoices/new.html',
        customers=customers,
        records=records,
        record_type = record_type,
        args={
            'customer': customer_id,
        }
    )

@BLUEPRINT.route('/<int:invoice_id>', methods=['GET', 'POST'])
def invoice(invoice_id):
    """Save comments and uploaded modified invoices."""
    cost_center = request.args.get('cost_center','KTH')
    invoice_obj = db.invoice(invoice_id)
    if request.method == 'POST':
        invoice_obj.comment = request.form.get('comment')
        if request.form.get('invoice_sent'):
            invoice_obj.invoiced_at = date.today()
        else:
            invoice_obj.invoiced_at = None

        kth_excel_file = request.files.get('KTH_excel')
        if kth_excel_file:
            invoice_obj.excel_kth = kth_excel_file.stream.read()
        ki_excel_file = request.files.get('KI_excel')
        if ki_excel_file:
            invoice_obj.excel_ki = ki_excel_file.stream.read()
        db.commit()
    api = InvoiceAPI(db, lims)
    invoice_dict = {'KTH' : api.prepare('KTH', invoice_obj), 
                    'KI' : api.prepare('KI', invoice_obj)}
    print(invoice_dict)
    print('h2h2hh2hh2')
    return render_template('invoices/invoice.html', 
                            invoice=invoice_obj, 
                            invoice_dict=invoice_dict)

@BLUEPRINT.route('/<int:invoice_id>/excel')
def invoice_template(invoice_id):
    """Generate invoice template"""
    cost_center = request.args.get('cost_center','KTH')
    invoice_obj = db.invoice(invoice_id)
    api = InvoiceAPI(db,lims)
    invoice_dict = api.prepare(cost_center, invoice_obj)
    workbook = render_xlsx(invoice_dict)

    temp_dir = tempfile.gettempdir()
    fname = "Invoice_{}_{}.xlsx".format(invoice_obj.id, cost_center)
    excel_path = os.path.join(temp_dir, fname)
    workbook.save(excel_path)

    return send_from_directory(directory=temp_dir, filename=fname, as_attachment=True)


@BLUEPRINT.route('/<int:invoice_id>/invoice_file/<cost_center>')
def modified_invoice(invoice_id, cost_center):
    """Enables download of modified invoices saved in the database."""
    invoice_obj = db.invoice(invoice_id)
    file_name = 'invoice_'+cost_center+str(invoice_id)+'.xlsx'
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, file_name)
    
    with open(file_path, 'wb') as file_object:
        if cost_center == 'KTH':
            file_object.write(invoice_obj.excel_kth)
        elif cost_center == 'KI':
            file_object.write(invoice_obj.excel_ki)
        pass
    return send_from_directory(directory=temp_dir, filename=file_name, as_attachment=True)
