import time
from datetime import datetime
from operator import itemgetter

import netsvc
from osv import fields, osv
from tools.translate import _
import decimal_precision as dp
import tools

class wizard_tax_oncharge(osv.osv_memory):
	_name = "wizard.tax.oncharge"
	_columns = {
		'tax_ids': fields.many2many('account.tax', 'ext_transaksi_tax_line_rel', 'ext_tax_line_id', 'tax_id', 'Taxes', domain=[('parent_id','=',False)]),
	}

	def create_extra_tax(self, cr, uid, ids, context=None):
		if context is None: context = {}
		ext_ids = context.get('active_ids', [])
		oncharge_obj = self.read(cr, uid, ids, ['tax_ids'])
		res={}
		if not ext_ids or len(ext_ids) != 1:
			return res
		ext = self.pool.get('ext.transaksi').browse(cr, uid, ext_ids, context=context)[0]
		tax_ext_obj = self.pool.get('ext.transaksi.line')
		curr_obj = self.pool.get('res.currency')
		tax_obj = self.pool.get('account.tax')
		taxes = tax_obj.browse(cr, uid, oncharge_obj[0]['tax_ids'], context=context)
		invoice_group = {}
		for line in ext.ext_line:
			if line.invoice_related_id:
				if line.picking_related_id:
					key = line.invoice_related_id.id,line.picking_related_id.id
					if key in invoice_group:
						invoice_group[key].update({
							line.id : line.debit
						})
					else:
						invoice_group.update({key:{}})
						invoice_group[key].update({
							line.id : line.debit
						})
				else:
					key = line.invoice_related_id.id
					if key in invoice_group:
						invoice_group[key].update({
							line.id : line.debit
						})
					else:
						invoice_group.update({key:{}})
						invoice_group[key].update({
							line.id : line.debit
						})
			else:
				invoice_group.update({'non-'+str(line.id):{}})
				invoice_group['non-'+str(line.id)].update({
					line.id : line.debit
				})
		
		tax_base_currency_ids = curr_obj.search(cr, uid, [('name','=','IDR')],context=context)
		tax_base_currency_id = False
		if tax_base_currency_ids:
			tax_base_currency_id = curr_obj.browse(cr, uid, tax_base_currency_ids, context=context)[0].id

		for x in invoice_group.keys():
			if len(str(x))>4 and str(x)[0:4] == 'non-':
				for line in ext.ext_line:
					if line.id == int(x[4:]) and line.debit!=0.0:
						for tax in tax_obj.compute_all(cr, uid, taxes,
								line.debit or 0.0,
								1.0, False,
								line.partner_id)['taxes']:
							name=tax['name']
							# round into 0 digit, coz Faktur Pajak, is always using 0 rounding
							amount = round(tax['amount'],0)
							base = curr_obj.round(cr, uid, ext.currency_id, line.debit)
							base_code_id = tax['base_code_id']
							tax_code_id = tax['tax_code_id']
							# base_amount = curr_obj.compute(cr, uid, ext.currency_id.id, company_currency, base * tax['base_sign'], context={'date': ext.date or time.strftime('%Y-%m-%d')}, round=False)
							# tax_amount = curr_obj.compute(cr, uid, ext.currency_id.id, company_currency, amount * tax['tax_sign'], context={'date': ext.date or time.strftime('%Y-%m-%d')}, round=False)
							account_id = tax['account_collected_id'] or line.account_id.id
							account_analytic_id = tax['account_analytic_collected_id']

							amount_currency = curr_obj.compute(cr, uid, ext.currency_id.id, tax_base_currency_id, amount, context={'date': ext.date or time.strftime('%Y-%m-%d')}, round=False)
							tax_ext_line_res = {
								'invoice_related_id' : False,
								'type_of_charge': line.type_of_charge and line.type_of_charge.id or False,
								'tax_ext_transaksi_id': line.ext_transaksi_id and line.ext_transaksi_id.id or False,
								'name' : name or '/',
								'debit': amount>0 and amount or 0.0,
								'credit': amount<0 and abs(amount) or 0.0,
								'account_id' : account_id,
								'department_id': line.department_id and line.department_id.id or False,
								'analytic_account_id': account_analytic_id and account_analytic_id or (line.analytic_account_id and line.analytic_account_id.id or False),
								'partner_id': line.partner_id and line.partner_id.id or False,
								'tax_base' : base,
								'tax_code_id' : tax_code_id,
								'amount_currency': amount_currency,
								'currency_id': tax_base_currency_id,
							}

							tax_ext_obj.create(cr, uid, tax_ext_line_res, context=context)
			else:
				total_debit = 0.0
				for y in invoice_group[x].keys():
					total_debit += invoice_group[x][y]

				for line in ext.ext_line:
					if line.id == invoice_group[x].keys()[0]:
						for tax in tax_obj.compute_all(cr, uid, taxes,
								total_debit or 0.0,
								1.0, False,
								line.partner_id)['taxes']:
							name=tax['name']
							amount = round(tax['amount'],0)
							# amount = tax['amount']
							base = curr_obj.round(cr, uid, ext.currency_id, total_debit)
							base_code_id = tax['base_code_id']
							tax_code_id = tax['tax_code_id']
							# base_amount = curr_obj.compute(cr, uid, ext.currency_id.id, company_currency, base * tax['base_sign'], context={'date': ext.date or time.strftime('%Y-%m-%d')}, round=False)
							# tax_amount = curr_obj.compute(cr, uid, ext.currency_id.id, company_currency, amount * tax['tax_sign'], context={'date': ext.date or time.strftime('%Y-%m-%d')}, round=False)
							account_id = tax['account_collected_id'] or line.account_id.id
							account_analytic_id = tax['account_analytic_collected_id']

							amount_currency = curr_obj.compute(cr, uid, ext.currency_id.id, tax_base_currency_id, amount, context={'date': ext.date or time.strftime('%Y-%m-%d')}, round=False)
							tax_ext_line_res = {
								'invoice_related_id' : line.invoice_related_id and line.invoice_related_id.id or False,
								'picking_related_id' : line.picking_related_id and line.picking_related_id.id or False,
								'type_of_charge': line.type_of_charge and line.type_of_charge.id or False,
								'tax_ext_transaksi_id': line.ext_transaksi_id and line.ext_transaksi_id.id or False,
								'name' : name or '/',
								'debit': amount>0 and amount or 0.0,
								'credit': amount<0 and abs(amount) or 0.0,
								'account_id' : account_id,
								'department_id': line.department_id and line.department_id.id or False,
								'analytic_account_id': account_analytic_id and account_analytic_id or (line.analytic_account_id and line.analytic_account_id.id or False),
								'partner_id': line.partner_id and line.partner_id.id or False,
								'tax_base' : base,
								'tax_code_id' : tax_code_id,
								'amount_currency': amount_currency,
								'currency_id': tax_base_currency_id,
							}

							tax_ext_obj.create(cr, uid, tax_ext_line_res, context=context)

		return True
