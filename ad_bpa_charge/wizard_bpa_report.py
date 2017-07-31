import time
import netsvc
from tools.translate import _
import tools
from datetime import datetime, timedelta
from osv import fields, osv
from dateutil.relativedelta import relativedelta
import decimal_precision as dp
from openerp import tools
from openerp.osv import fields,osv
from openerp.addons.decimal_precision import decimal_precision as dp

class bpa_summary(osv.osv):
	_name = "bpa.summary"
	_description = "BPA Summary"
	_auto = False

	_columns = {
		'type_of_charge': fields.many2one('charge.type','Charge For',readonly=True),
		'invoice_id':fields.many2one('account.invoice', 'Invoice Charge', readonly=True),
		'state' : fields.related('invoice_id', 'state', type='selection', selection=[
			('draft','Draft'),
			('proforma','Pro-forma'),
			('proforma2','Invoice Released'),
			('open','AR/AP Outstanding'),
			('paid','Paid'),
			('cancel','Cancelled'),
			], string="State", readonly=True),
		'reference':fields.related('invoice_id','reference', type='char', size=64, readonly=True, string='Payment Reference'),
		'bill_date':fields.date('Bill Date',readonly=True),
		'due_date':fields.date('Due Date',readonly=True),
		'invoice_related_id':fields.many2one('account.invoice', 'Commercial Invoice', readonly=True),
		'bl_number':fields.char('BL Number',readonly=True),
		'bl_date':fields.date('BL Date',readonly=True),
		'picking_related_id':fields.many2one('stock.picking', 'Shipment', readonly=True),
		'date_done':fields.related('picking_related_id', 'date_done', type='datetime', string="Date Transfer", readonly=True),
		'partner_id':fields.many2one('res.partner', 'Carrier', readonly=True),
		'currency_id':fields.many2one('res.currency', 'Currency', readonly=True),
		'amount':fields.float('Amount',readonly=True),
	}

	def init(self, cr):
		tools.drop_view_if_exists(cr, 'bpa_summary')
		cr.execute("""
			CREATE OR REPLACE view bpa_summary AS (
				SELECT 
					row_number() OVER () as id,
					a.type_of_charge,
					d.id as invoice_id, 
					d.date_invoice as bill_date, 
					d.date_due as due_date, 
					b.id as invoice_related_id, 
					b.bl_number, 
					b.bl_date, 
					a.picking_related_id, 
					d.partner_id, 
					d.currency_id, 
					sum(a.price_subtotal) as amount
				FROM
					account_invoice_line a
					LEFT JOIN account_invoice b ON b.id=a.invoice_related_id
					LEFT JOIN stock_picking c ON c.id=a.picking_related_id 
					LEFT JOIN account_invoice d ON d.id=a.invoice_id 
				WHERE
					d.type='in_invoice' and a.type_of_charge is not NULL and d.state not in ('cancel')
				GROUP BY
					d.id, d.partner_id, a.picking_related_id, b.id, 
					b.bl_number, b.bl_date, d.date_invoice, 
					d.date_due, d.currency_id, a.type_of_charge
				ORDER BY
					d.partner_id, a.picking_related_id, b.id
					   )
		""")
bpa_summary()

class wizard_bpa_report(osv.osv_memory):
	_name = "wizard.bpa.report"
	_columns = {
			"type_of_charge"	: fields.many2one('charge.type','Charge For',required=True),
			"reference"			: fields.char('BPA Number',size=64,required=True),
	}
	_defaults = {
	}

	def print_report(self, cr, uid, ids, context={}):
		datas = {
			 'ids': context.get('active_ids',[]),
			 'model': 'wizard.bpa.report',
			 'form': self.read(cr, uid, ids)[0],
			}

		if datas['form']['type_of_charge'][1].encode('utf-8').upper() in ('FREIGHT'):
			return {
					'type': 'ir.actions.report.xml',
					'report_name': 'bpa.report.freight.mako',
					'report_type': 'webkit',
					'datas': datas,
				}
		elif datas['form']['type_of_charge'][1].encode('utf-8').upper() in ('SALES COMMISSION'):
			return {
					'type': 'ir.actions.report.xml',
					'report_name': 'bpa.report.comm.mako',
					'report_type': 'webkit',
					'datas': datas,
				}
		elif datas['form']['type_of_charge'][1].encode('utf-8').upper() in ('EMKL','LIFT ON LIFT OFF','TRANSPORT'):
			return {
					'type': 'ir.actions.report.xml',
					'report_name': 'bpa.report.emkl.mako',
					'report_type': 'webkit',
					'datas': datas,
				}
		elif datas['form']['type_of_charge'][1].encode('utf-8').upper() in ('[FGHE] FINISH GOOD HANDLING EXPORT','[FGHL] FINISH GOOD HANDLING LOCAL'):
			return {
					'type': 'ir.actions.report.xml',
					'report_name': 'bpa.report.kbkb.mako',
					'report_type': 'webkit',
					'datas': datas,
				}
		
wizard_bpa_report()