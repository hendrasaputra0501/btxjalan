from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
from openerp.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp


class account_invoice_commission_line(osv.osv):
	def _get_commission_invoice_line(self, cr, uid, ids, context=None):
		res=[]
		for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
			if line.invoice_id:
				if line.invoice_id.commission_ids:
					for commission in line.invoice_id.commission_ids:
						for line in commission.commission_lines:
							if line.id not in res:
								res.append(line.id)
		return res
	
	def _get_commission_invoice_tax(self, cr, uid, ids, context=None):
		res=[]
		for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
			if tax.invoice_id:
				if tax.invoice_id.commission_ids:
					for commission in tax.invoice_id.commission_ids:
						for line in commission.commission_lines:
							if line.id not in res:
								res.append(line.id)
		return res

	def _get_ratio(self, cr, uid, ids, field_names, arg=None, context=None):
		result = {}
		if not ids: return result
		
		for line in self.browse(cr,uid,ids):
			if line.commission_id and line.commission_id.invoice_id and line.commission_id.invoice_id.invoice_line:
				result[line.id] = 0.0
				for inv_line in line.commission_id.invoice_id.invoice_line:
					if inv_line.move_line_ids and inv_line.move_line_ids[0].sale_line_id and line.sale_order_agent_id and line.sale_order_agent_id.sale_line_id and inv_line.move_line_ids[0].sale_line_id.id==line.sale_order_agent_id.sale_line_id.id:
						result[line.id] += inv_line.price_subtotal / inv_line.invoice_id.amount_untaxed
		return result

	def _get_sale_order_agent(self, cr, uid, ids, context=None):
		sale_order_agent_ids = [x.id for x in self.pool.get('sale.order.agent').browse(cr,uid,ids,context=context)]
		query = "SELECT id FROM account_invoice_commission_line WHERE sale_order_agent_id in ("+(','.join([str(int(x)) for x in sale_order_agent_ids]))+")"
		cr.execute(query)
		res = cr.fetchall()
		if res:
			res=[x[0] for x in res]
		return res

	def _get_invoice_partner_id(self, cr, uid, ids, field_names, arg=None, context=None):
		result = {}
		if not ids: return result
		for line in self.browse(cr,uid,ids):
			partner=False
			agent=False
			if not (partner or agent) and line.sale_order_agent_id:
				agent=line.sale_order_agent_id.agent_id and line.sale_order_agent_id.agent_id.id or False
				partner=line.sale_order_agent_id.invoice_partner_id and line.sale_order_agent_id.invoice_partner_id.id or False
			if not (partner or agent):
				raise osv.except_osv(_('Trigger Error !'),
					_('Please define the partner for pay the commission !'))
			result.update({line.id:{"invoice_partner_id":partner,"agent_id":agent}})
		return result

	def _get_percentage_from_sale_order_agent(self, cr, uid, ids, field_names, arg=None, context=None):
		result = {}
		if not ids: return result
		for line in self.browse(cr,uid,ids):
			percentage=0.0
			if line.sale_order_agent_id:
				percentage=line.sale_order_agent_id.commission_percentage
			result.update({line.id:percentage})
		return result

	def _get_amount_commission_per_agent(self, cr, uid, ids, field_names, arg=None, context=None):
		result = {}
		if not ids: return result
		
		for line in self.browse(cr,uid,ids):
			result[line.id] = {
				'commission_amount_fob': 0.0,
				'commission_amount_actual': 0.0,
			}
			is_incoterm = False
			if line.commission_id:
				if line.commission_id.invoice_id:
					if line.commission_id.invoice_id.sale_ids:
						for sale in line.commission_id.invoice_id.sale_ids:
							if sale.incoterm:
								is_incoterm = True

			if is_incoterm:
				result[line.id]['commission_amount_fob']=(line.commission_percentage/100)*line.commission_id.invoice_id.amount_fob*line.ratio_of_amount
				result[line.id]['commission_amount_actual']=(line.commission_percentage/100)*line.commission_id.invoice_id.amount_untaxed*line.ratio_of_amount
			else:
				result[line.id]['commission_amount_fob']=(line.commission_percentage/100)*line.commission_id.invoice_id.amount_total*line.ratio_of_amount
				result[line.id]['commission_amount_actual']=(line.commission_percentage/100)*line.commission_id.invoice_id.amount_untaxed*line.ratio_of_amount
		return result

	def _get_account_invoice_charge(self,cr,uid,ids,context=None):
		if not context:context={}
		res = []

		for inv in self.pool.get('account.invoice').browse(cr,uid,ids,context=context):
			if inv.invoice_line:
				for line in inv.invoice_line:
					if line.invoice_related_id:
						if line.invoice_related_id.commission_ids:
							for commission in line.invoice_related_id.commission_ids:
								for line in commission.commission_lines:
									if line.id not in res:
										res.append(line.id)
		return res

	def _get_invoice_charge_line(self, cr, uid, ids, context=None):
		if not context:context={}
		res = []
		for line in self.pool.get('account.invoice.line').browse(cr,uid,ids,context=context):
			if line.invoice_related_id:
				if line.invoice_related_id.commission_ids:
					for commission in line.invoice_related_id.commission_ids:
						for line in commission.commission_lines:
							if line.id not in res:
								res.append(line.id)
		return res

	def _get_ext_transaksi_charge(self,cr,uid,ids,context=None):
		if not context:context={}
		res = []

		for bpa in self.pool.get('ext.transaksi').browse(cr,uid,ids,context=context):
			if bpa.ext_line:
				for line in bpa.ext_line:
					if line.invoice_related_id:
						if line.invoice_related_id.commission_ids:
							for commission in line.invoice_related_id.commission_ids:
								for line in commission.commission_lines:
									if line.id not in res:
										res.append(line.id)
		return res

	def _get_ext_transaksi_charge_line(self,cr,uid,ids,context=None):
		if not context:context={}
		res = []

		for line in self.pool.get('ext.transaksi.line').browse(cr,uid,ids,context=context):
			if line.invoice_related_id:
				if line.invoice_related_id.commission_ids:
					for commission in line.invoice_related_id.commission_ids:
						for line in commission.commission_lines:
							if line.id not in res:
								res.append(line.id)
		return res

	_name = "account.invoice.commission.line"
	_rec_name = "sale_order_agent_id"
	_columns = {
		"commission_id" : fields.many2one('account.invoice.commission','Commission',ondelete='cascade'),
		"sale_order_agent_id" : fields.many2one('sale.order.agent','Sales Agent',ondelete='cascade'),
		"ratio_of_amount" : fields.function(_get_ratio, type='float', digits=(0,11), string='Ratio Amount in Invoice', method=True,
			store={
				'account.invoice.commission.line':(lambda self,cr,uid,ids,context={}:ids,['sale_order_agent_id','commission_id'],10),
				'account.invoice.line': (_get_commission_invoice_line, ['price_unit','invoice_line_tax_id','quantity','invoice_id'], 21),
				'account.invoice.tax': (_get_commission_invoice_tax, None, 21),
			}),
		"agent_id" : fields.function(_get_invoice_partner_id, type='many2one', method=True,obj='res.partner', string='Agent', 
			store={
				'account.invoice.commission.line':(lambda self,cr,uid,ids,context={}:ids,['sale_order_agent_id','commission_id'],10),
				# basic commision datas from sales contract : agent, payment to, percentage
				'sale.order.agent' : (_get_sale_order_agent, ['agent_id'], 21),
			}, multi="line_agent_all"),
		"invoice_partner_id" : fields.function(_get_invoice_partner_id, type='many2one', method=True,obj='res.partner', string='Payment To', 
			store={
				'account.invoice.commission.line':(lambda self,cr,uid,ids,context={}:ids,['sale_order_agent_id','commission_id'],10),
				# basic commision datas from sales contract : agent, payment to, percentage
				'sale.order.agent' : (_get_sale_order_agent, ['invoice_partner_id'], 21),
			}, multi="line_agent_all"),
		"commission_percentage" : fields.function(_get_percentage_from_sale_order_agent,type='float', method=True, string='Commission Percentage', digits_compute=dp.get_precision('Commission Amount'),
			store={
				'account.invoice.commission.line':(lambda self,cr,uid,ids,context={}:ids,['sale_order_agent_id','commission_id'],10),
				# basic commision datas from sales contract : agent, payment to, percentage
				'sale.order.agent' : (_get_sale_order_agent, ['agent_id','invoice_partner_id','commission_percentage'], 21),
			}),
		"commission_amount_fob" : fields.function(_get_amount_commission_per_agent,type='float', method=True, string='Commission Amount', digits_compute=dp.get_precision('Account'),
			store={
				'account.invoice.commission.line':(lambda self,cr,uid,ids,context={}:ids,['sale_order_agent_id','commission_id'],11),
				# basic commision datas from sales contract : agent, payment to, percentage
				'sale.order.agent' : (_get_sale_order_agent, ['agent_id','invoice_partner_id','commission_percentage'], 22),
				# actual charge realisation, to compute amount fob : invoice charge and extra payment
				'account.invoice' : (_get_account_invoice_charge, ['state','invoice_line'], 21),
				'account.invoice.line': (_get_invoice_charge_line, ['price_unit','invoice_line_tax_id','quantity','invoice_related_id'], 23),
				'ext.transaksi' : (_get_ext_transaksi_charge, ['state','ext_line','tax_ext_line'], 21),
				'ext.transaksi.line' : (_get_ext_transaksi_charge_line, ['debit','credit','invoice_related_id'], 21),
				# actual rate invoice, to compute amount fob : invoice line and invoice tax line
				'account.invoice.line': (_get_commission_invoice_line, ['price_unit','invoice_line_tax_id','quantity','invoice_id'], 22),
				'account.invoice.tax': (_get_commission_invoice_tax, None, 22),
			}, multi='line_all_agent_commission'),
		"commission_amount_actual" : fields.function(_get_amount_commission_per_agent,type='float', method=True, string='Commission Amount Exclude Fob', digits_compute=dp.get_precision('Account'),
			store={
				'account.invoice.commission.line':(lambda self,cr,uid,ids,context={}:ids,['sale_order_agent_id','commission_id'],11),
				# basic commision datas from sales contract : agent, payment to, percentage
				'sale.order.agent' : (_get_sale_order_agent, ['agent_id','invoice_partner_id','commission_percentage'], 22),
				# actual charge realisation, to compute amount fob : invoice charge and extra payment
				'account.invoice' : (_get_account_invoice_charge, ['state','invoice_line'], 21),
				'account.invoice.line': (_get_invoice_charge_line, ['price_unit','invoice_line_tax_id','quantity','invoice_related_id'], 23),
				'ext.transaksi' : (_get_ext_transaksi_charge, ['state','ext_line','tax_ext_line'], 21),
				'ext.transaksi.line' : (_get_ext_transaksi_charge_line, ['debit','credit','invoice_related_id'], 21),
				# actual rate invoice, to compute amount fob : invoice line and invoice tax line
				'account.invoice.line': (_get_commission_invoice_line, ['price_unit','invoice_line_tax_id','quantity','invoice_id'], 22),
				'account.invoice.tax': (_get_commission_invoice_tax, None, 22),
			}, multi='line_all_agent_commission'),
	}

account_invoice_commission_line()


class account_invoice_commission(osv.osv):
	_name = "account.invoice.commission"

	def _get_sale_order_agent(self, cr, uid, ids, context=None):
		res=[]
		
		sale_order_agent_ids = [x.id for x in self.pool.get('sale.order.agent').browse(cr,uid,ids,context=context)]
		query = "SELECT commission_id FROM account_invoice_commission_line WHERE sale_order_agent_id in ("+(','.join([str(int(x)) for x in sale_order_agent_ids]))+")"
		cr.execute(query)
		res = cr.fetchall()
		if res:
			res=[x[0] for x in res]
		return res

	def _get_invoice_partner_id(self, cr, uid, ids, field_names, arg=None, context=None):
		result = {}
		if not ids: return result
		for commission in self.browse(cr,uid,ids):
			partner=False
			agent=False
			# if line.sale_order_agent_ids:
			# 	agent=line.sale_order_agent_ids[0].agent_id and line.sale_order_agent_ids[0].agent_id.id or False
			# 	partner=line.sale_order_agent_ids[0].invoice_partner_id and line.sale_order_agent_ids[0].invoice_partner_id.id or False
			if not (partner or agent):
				agent=commission.commission_lines and  commission.commission_lines[0].agent_id and commission.commission_lines[0].agent_id.id or False
				partner=commission.commission_lines and  commission.commission_lines[0].invoice_partner_id and commission.commission_lines[0].invoice_partner_id.id or False
			if not (partner or agent):
				raise osv.except_osv(_('Trigger Error !'),
					_('Please define the partner for pay the commission !'))
			result.update({commission.id:{"invoice_partner_id":partner,"agent_id":agent}})
		return result

	def _get_percentage_from_sale_order_agent(self, cr, uid, ids, field_names, arg=None, context=None):
		result = {}
		if not ids: return result
		for commission in self.browse(cr,uid,ids):
			percentage=0.0
			if commission.commission_lines:
				for line in commission.commission_lines:
					percentage+=line.commission_percentage or 0.0
				percentage = percentage/len(commission.commission_lines)
			result.update({commission.id:percentage})
		return result

	def _get_account_invoice_charge(self,cr,uid,ids,context=None):
		if not context:context={}
		res = []

		for inv in self.pool.get('account.invoice').browse(cr,uid,ids,context=context):
			if inv.invoice_line:
				for line in inv.invoice_line:
					if line.invoice_related_id:
						if line.invoice_related_id.commission_ids:
							for commission in line.invoice_related_id.commission_ids:
								if commission.id not in res:
									res.append(commission.id)
		return res

	def _get_invoice_charge_line(self, cr, uid, ids, context=None):
		if not context:context={}
		res = []
		for line in self.pool.get('account.invoice.line').browse(cr,uid,ids,context=context):
			if line.invoice_related_id:
				if line.invoice_related_id.commission_ids:
					for commission in line.invoice_related_id.commission_ids:
						if commission.id not in res:
							res.append(commission.id)
		return res

	def _get_ext_transaksi_charge(self,cr,uid,ids,context=None):
		if not context:context={}
		res = []

		for bpa in self.pool.get('ext.transaksi').browse(cr,uid,ids,context=context):
			if bpa.ext_line:
				for line in bpa.ext_line:
					if line.invoice_related_id:
						if line.invoice_related_id.commission_ids:
							for commission in line.invoice_related_id.commission_ids:
								if commission.id not in res:
									res.append(commission.id)
		return res

	def _get_ext_transaksi_charge_line(self,cr,uid,ids,context=None):
		if not context:context={}
		res = []

		for line in self.pool.get('ext.transaksi.line').browse(cr,uid,ids,context=context):
			if line.invoice_related_id:
				if line.invoice_related_id.commission_ids:
					for commission in line.invoice_related_id.commission_ids:
						if commission.id not in res:
							res.append(commission.id)
		return res

	def _get_commission_invoice_line(self, cr, uid, ids, context=None):
		res=[]
		for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
			if line.invoice_id:
				if line.invoice_id.commission_ids:
					for commission in line.invoice_id.commission_ids:
						if commission.id not in res:
							res.append(commission.id)
		return res
	
	def _get_commission_invoice_tax(self, cr, uid, ids, context=None):
		res=[]
		for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
			if tax.invoice_id:
				if tax.invoice_id.commission_ids:
					for commission in tax.invoice_id.commission_ids:
						if commission.id not in res:
							res.append(commission.id)
		return res

	def _get_amount_commission_per_agent(self, cr, uid, ids, field_names, arg=None, context=None):
		result = {}
		if not ids: return result
		
		for commission in self.browse(cr,uid,ids):
			result[commission.id] = {
				'commission_amount': 0.0,
				'commission_amount_without_fob': 0.0,
			}

			for line in commission.commission_lines:
				result[commission.id]['commission_amount']+=line.commission_amount_fob
				result[commission.id]['commission_amount_without_fob']+=line.commission_amount_actual

			# is_incoterm = False
			# if line.invoice_id:
			# 	if line.invoice_id.sale_ids:
			# 		for sale in line.invoice_id.sale_ids:
			# 			if sale.incoterm:
			# 				is_incoterm = True
			# if is_incoterm:
			# 	result[line.id]['commission_amount']=(line.commission_percentage/100)*line.invoice_id.amount_fob
			# 	result[line.id]['commission_amount_without_fob']=(line.commission_percentage/100)*line.invoice_id.amount_total
			# else:
			# 	result[line.id]['commission_amount']=(line.commission_percentage/100)*line.invoice_id.amount_total
			# 	result[line.id]['commission_amount_without_fob']=(line.commission_percentage/100)*line.invoice_id.amount_total
		return result

	def _get_payments(self,cr,uid,ids,context=None):
		if not context:context={}
		res = []
		for trans in self.pool.get('ext.transaksi').browse(cr,uid,ids,context=context):
			if trans.ext_line:
				for line in trans.ext_line:
					if line.commission_id:
						if line.commission_id.id not in res:
							res.append(line.commission_id.id)
		return res

	def _get_account_invoice_chg(self,cr,uid,ids,context=None):
		""" 
		This function is to get the account invoice of this commision outstanding that already valid
		or accrued and have had payable journal
		"""
		if not context:context={}
		res = []

		for inv in self.pool.get('account.invoice').browse(cr,uid,ids,context=context):
			if inv.bill_id:
				for bill_line in inv.bill_id.bill_lines:
					if bill_line.invoice_id == inv:
						comm_id = False
						if bill_line.comm_id:
							comm_id = bill_line.comm_id.id
						elif bill_line.comm_provision_id:
							comm_id = bill_line.comm_provision_id.id
						if comm_id and comm_id not in res:
							res.append(comm_id)
		return res

	def _get_invoice_from_line(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		res = []
		move = {}
		for line in self.pool.get('account.move.line').browse(cr, uid, ids, context=context):
			if line.reconcile_partial_id:
				for line2 in line.reconcile_partial_id.line_partial_ids:
					move[line2.move_id.id] = True
			if line.reconcile_id:
				for line2 in line.reconcile_id.line_id:
					move[line2.move_id.id] = True
		invoice_ids = []
		if move:
			invoice_ids = self.pool.get('account.invoice').search(cr, uid, [('move_id','in',move.keys())], context=context)
			if invoice_ids:
				for inv in self.pool.get('account.invoice').browse(cr, uid, invoice_ids, context=context):
					if inv.bill_id:
						for bill_line in inv.bill_id.bill_lines:
							if bill_line.invoice_id == inv:
								comm_id = False
								if bill_line.comm_id:
									comm_id = bill_line.comm_id.id
								elif bill_line.comm_provision_id:
									comm_id = bill_line.comm_provision_id.id
								if comm_id and comm_id not in res:
									res.append(comm_id)
		return res

	def _get_invoice_from_reconcile(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		res = []
		move = {}
		for line in self.pool.get('account.move.reconcile').browse(cr, uid, ids, context=context):
			for mvl_line in line.line_partial_ids:
				move[mvl_line.move_id.id] = True
			for mvl_linex in line.line_id:
				move[mvl_linex.move_id.id] = True

		invoice_ids = []
		if move:
			invoice_ids = self.pool.get('account.invoice').search(cr, uid, [('move_id','in',move.keys())], context=context)
			if invoice_ids:
				for inv in self.pool.get('account.invoice').browse(cr, uid, invoice_ids, context=context):
					if inv.bill_id:
						for bill_line in inv.bill_id.bill_lines:
							if bill_line.invoice_id == inv:
								comm_id = False
								if bill_line.comm_id:
									comm_id = bill_line.comm_id.id
								elif bill_line.comm_provision_id:
									comm_id = bill_line.comm_provision_id.id
								if comm_id and comm_id not in res:
									res.append(comm_id)
		return res

	def _get_amount_status_comm(self, cr, uid, ids, field_names, arg=None, context=None):
		if context is None:
			context = {}

		result = {}
		if not ids: return result
		for commission in self.browse(cr,uid,ids):
			result[commission.id] = {
				'amount_invoiced': 0.0,
				'amount_paid': 0.0,
				'amount_outstanding':0.0,
				'state':'open',
				'date_done':False,
			}
			amount_invoiced = 0.0
			amount_paid = 0.0
			amount_outstanding = round(commission.commission_amount,2)
			invoice_lines = []
			provision_paid = False
			provision_paid_date = False
			if commission.invoice_prov_id and commission.invoice_prov_id.state in ('open','paid') and commission.invoice_prov_line_id:
				invoice_lines.append(commission.invoice_prov_line_id)
			for bill in commission.bill_ids:
				print "aaaaaaaaaa", bill.bill_id.state, bill.invoice_id.id, commission.invoice_prov_id.id, bill.invoice_line_id.id, commission.invoice_prov_line_id.id
				if commission.invoice_prov_id and commission.invoice_prov_id.state in ('open','paid') \
					and commission.invoice_prov_line_id and bill.invoice_id and bill.invoice_id.id==commission.invoice_prov_id.id and \
					bill.invoice_line_id and bill.invoice_line_id.id==commission.invoice_prov_line_id.id and bill.bill_id.state=='confirmed':
					print "bbbbbbbbbbbb"	
					provision_paid = True
					provision_paid_date = bill.bill_id.date_effective

				if bill.invoice_id and bill.invoice_id.state in ('open','paid') and bill.invoice_line_id and bill.invoice_line_id not in invoice_lines:
					invoice_lines.append(bill.invoice_line_id)
			to_currency = commission.invoice_id.currency_id.id
			if invoice_lines:
				for inv_line in invoice_lines:
					# if inv_line.invoice_id and inv_line.invoice_id.state=='paid':
					from_currency = inv_line.invoice_id.currency_id.id
					context.update({'date':inv_line.invoice_id.date_invoice or time.strftime('%Y-%m-%d')})
					amt_inv_paid = inv_line.invoice_id.amount_total - inv_line.invoice_id.residual
					amt_inv_paid = self.pool.get('res.currency').compute(cr, uid, from_currency, to_currency, amt_inv_paid, context=context)
					# amount_paid += (inv_line.price_subtotal+inv_line.tax_amount)/inv_line.invoice_id.amount_total * amt_inv_paid
					amount_paid += inv_line.price_subtotal/inv_line.invoice_id.amount_untaxed * amt_inv_paid
					amount_outstanding -= amount_paid
					
					# amt_invced = (inv_line.price_subtotal or 0.0)+(inv_line.tax_amount or 0.0)
					amt_invced = inv_line.price_subtotal or 0.0
					amt_invced = self.pool.get('res.currency').compute(cr, uid, from_currency, to_currency, amt_invced, context=context)
					amount_invoiced += amt_invced
					# elif inv_line.invoice_id:
					# 	from_currency = inv_line.invoice_id.currency_id.id
					# 	amt_invced = (inv_line.price_subtotal or 0.0)+(inv_line.tax_amount or 0.0)
					# 	amt_invced = self.pool.get('res.currency').compute(cr, uid, from_currency, to_currency, amt_invced, context=context)
					# 	amount_invoiced += amt_invced
			result[commission.id]['amount_invoiced']=amount_invoiced
			result[commission.id]['amount_paid']=amount_paid
			if amount_outstanding>=0:
				result[commission.id]['amount_outstanding']=amount_outstanding
			if provision_paid:
				result[commission.id]['state']='paid'
				result[commission.id]['date_done']=provision_paid_date
			elif amount_outstanding<=0 or amount_paid>0:
				result[commission.id]['state']='paid'
				invoice_objs = [x.invoice_id for x in invoice_lines]
				acc_move_objs = [x.move_id for x in invoice_objs]
				last_effective_date = False
				last_move_obj = False
				for move in acc_move_objs:
					if not last_effective_date or last_effective_date<move.date:
						last_effective_date = move.date
						last_move_obj = move
				reconciliations = False
				move_id_comm = False
				if last_move_obj:
					for line_obj1 in last_move_obj.line_id:
						if line_obj1.reconcile_id or line_obj1.reconcile_partial_id:
							reconciliations = line_obj1.reconcile_id or line_obj1.reconcile_partial_id
							move_id_comm = line_obj1.id
					last_payment_date = False
					if reconciliations and move_id_comm:
						for line_obj2 in reconciliations.line_id+reconciliations.line_partial_ids:
							if line_obj2.id!=move_id_comm and (not last_payment_date or last_payment_date<line_obj2.date):
								last_payment_date = line_obj2.date
					if last_payment_date:
						result[commission.id]['date_done']=last_payment_date
				else:
					result[commission.id]['date_done']=commission.invoice_id.date_invoice

		return result

	_rec_name = "invoice_id"
	_columns = {
		"invoice_id" : fields.many2one('account.invoice','Invoice',ondelete='cascade'),
		"commission_lines" : fields.one2many('account.invoice.commission.line','commission_id','Commission Lines'),
		# "sale_order_agent_id" : fields.many2one('sale.order.agent','Sales Agent'),
		"agent_id" : fields.function(_get_invoice_partner_id, type='many2one', method=True,obj='res.partner', string='Agent', 
			store={
				# basic commision datas from sales contract : agent, payment to, percentage
				'account.invoice.commission' : (lambda self, cr, uid, ids, c={}: ids,['commission_lines','state'],19),
				'sale.order.agent' : (_get_sale_order_agent, ['agent_id'], 22),
			}, multi="agent_all"),
		"invoice_partner_id" : fields.function(_get_invoice_partner_id, type='many2one', method=True,obj='res.partner', string='Payment To', 
			store={
				# basic commision datas from sales contract : agent, payment to, percentage
				'account.invoice.commission' : (lambda self, cr, uid, ids, c={}: ids,['commission_lines','state'],19),
				'sale.order.agent' : (_get_sale_order_agent, ['invoice_partner_id'], 22),
			}, multi="agent_all"),
		"commission_percentage" : fields.function(_get_percentage_from_sale_order_agent,type='float', method=True, string='Commission Percentage', digits_compute=dp.get_precision('Commission Amount'),
			store={
				# basic commision datas from self oject : commission_lines
				'account.invoice.commission' : (lambda self, cr, uid, ids, c={}: ids,['commission_lines','state'],19),
				# basic commision datas from sales contract : agent, payment to, percentage
				'sale.order.agent' : (_get_sale_order_agent, ['agent_id','invoice_partner_id','commission_percentage'], 22),
			}),
		"commission_amount" : fields.function(_get_amount_commission_per_agent,type='float', method=True, string='Commission Amount FOB', digits_compute=dp.get_precision('Account'),
			store={
				# basic commision datas from self oject : commission_lines
				'account.invoice.commission' : (lambda self, cr, uid, ids, c={}: ids,['commission_lines','state','bill'],20),
				# basic commision datas from sales contract : agent, payment to, percentage
				'sale.order.agent' : (_get_sale_order_agent, ['agent_id','invoice_partner_id','commission_percentage'], 23),
				# actual charge realisation, to compute amount fob : invoice charge and extra payment
				'account.invoice' : (_get_account_invoice_charge, ['state','invoice_line'], 22),
				'account.invoice.line': (_get_invoice_charge_line, ['price_unit','invoice_line_tax_id','quantity','invoice_related_id'], 24),
				'ext.transaksi' : (_get_ext_transaksi_charge, ['state','ext_line','tax_ext_line'], 22),
				'ext.transaksi.line' : (_get_ext_transaksi_charge_line, ['debit','credit','invoice_related_id'], 22),
				# actual rate invoice, to compute amount fob : invoice line and invoice tax line
				'account.invoice.line': (_get_commission_invoice_line, ['price_unit','invoice_line_tax_id','quantity','invoice_id'], 23),
				'account.invoice.tax': (_get_commission_invoice_tax, None, 23),
			}, multi='all_agent_commission'),
		"commission_amount_without_fob" : fields.function(_get_amount_commission_per_agent,type='float', method=True, string='Commission Amount Actual', digits_compute=dp.get_precision('Account'),
			store={
				# basic commision datas from self oject : commission_lines
				'account.invoice.commission' : (lambda self, cr, uid, ids, c={}: ids,['commission_lines','state'],20),
				# basic commision datas from sales contract : agent, payment to, percentage
				'sale.order.agent' : (_get_sale_order_agent, ['agent_id','invoice_partner_id','commission_percentage'], 23),
				# actual charge realisation, to compute amount fob : invoice charge and extra payment
				'account.invoice' : (_get_account_invoice_charge, ['state','invoice_line'], 22),
				'account.invoice.line': (_get_invoice_charge_line, ['price_unit','invoice_line_tax_id','quantity','invoice_related_id'], 24),
				'ext.transaksi' : (_get_ext_transaksi_charge, ['state','ext_line','tax_ext_line'], 22),
				'ext.transaksi.line' : (_get_ext_transaksi_charge_line, ['debit','credit','invoice_related_id'], 22),
				# actual rate invoice, to compute amount fob : invoice line and invoice tax line
				'account.invoice.line': (_get_commission_invoice_line, ['price_unit','invoice_line_tax_id','quantity','invoice_id'], 23),
				'account.invoice.tax': (_get_commission_invoice_tax, None, 23),
			}, multi='all_agent_commission'),

		# new concept
		"bill_prov_id" : fields.many2one('account.bill.passing.line','Bill Passing Provision'),
		"invoice_prov_id" : fields.many2one('account.invoice','Invoice Provision'),
		"invoice_prov_line_id" : fields.many2one('account.invoice.line','Invoice Provision Line'),
		
		"bill_ids" : fields.one2many('account.bill.passing.line', 'comm_id', 'Bill Passing'),
		#>>>> include invoice id dan invoice_line_id yang ada di bill_id
		"amount_invoiced" : fields.function(_get_amount_status_comm, type='float', method=True, string='Amount Invoiced', digits_compute=dp.get_precision('Account'),
			store={
				# basic commision datas from self oject : commission_lines
				'account.invoice.commission' : (lambda self, cr, uid, ids, c={}: ids,['commission_lines','state'],21),
				# basic commision datas from sales contract : agent, payment to, percentage
				'sale.order.agent' : (_get_sale_order_agent, ['agent_id','invoice_partner_id','commission_percentage'], 24),
				# actual charge realisation, to compute amount fob : invoice charge and extra payment
				'account.invoice' : (_get_account_invoice_charge, ['state','invoice_line'], 23),
				'account.invoice.line': (_get_invoice_charge_line, ['price_unit','invoice_line_tax_id','quantity','invoice_related_id'], 25),
				'ext.transaksi' : (_get_ext_transaksi_charge, ['state','ext_line','tax_ext_line'], 23),
				'ext.transaksi.line' : (_get_ext_transaksi_charge_line, ['debit','credit','invoice_related_id'], 23),
				# actual rate invoice, to compute amount fob : invoice line and invoice tax line
				'account.invoice.line': (_get_commission_invoice_line, ['price_unit','invoice_line_tax_id','quantity','invoice_id'], 24),
				'account.invoice.tax': (_get_commission_invoice_tax, None, 24),
				# commision realisation : invoice charge created from bill passing
				'account.invoice' : (_get_account_invoice_chg, ['state'],23),
			}, multi='comm_state'),
		"amount_paid" : fields.function(_get_amount_status_comm, type='float', method=True, string='Amount Paid', digits_compute=dp.get_precision('Account'),
			store={
				# basic commision datas from self oject : commission_lines
				'account.invoice.commission' : (lambda self, cr, uid, ids, c={}: ids,['commission_lines','state','bill_ids'],21),
				# basic commision datas from sales contract : agent, payment to, percentage
				'sale.order.agent' : (_get_sale_order_agent, ['agent_id','invoice_partner_id','commission_percentage'], 24),
				# actual charge realisation, to compute amount fob : invoice charge and extra payment
				'account.invoice' : (_get_account_invoice_charge, ['state','invoice_line'], 23),
				'account.invoice.line': (_get_invoice_charge_line, ['price_unit','invoice_line_tax_id','quantity','invoice_related_id'], 25),
				'ext.transaksi' : (_get_ext_transaksi_charge, ['state','ext_line','tax_ext_line'], 23),
				'ext.transaksi.line' : (_get_ext_transaksi_charge_line, ['debit','credit','invoice_related_id'], 23),
				# actual rate invoice, to compute amount fob : invoice line and invoice tax line
				'account.invoice.line': (_get_commission_invoice_line, ['price_unit','invoice_line_tax_id','quantity','invoice_id'], 24),
				'account.invoice.tax': (_get_commission_invoice_tax, None, 24),
				# commision realisation : invoice charge created from bill passing
				'account.invoice' : (_get_account_invoice_chg, ['state'],23),
				# commision realisation payment : invoice move that have reconciled
				'account.move.line': (_get_invoice_from_line, None, 55),
				'account.move.reconcile': (_get_invoice_from_reconcile, None, 55),
			}, multi='comm_state'),
		"amount_outstanding" : fields.function(_get_amount_status_comm, type='float', method=True, string='Amount Outstanding', digits_compute=dp.get_precision('Account'),
			store={
				# basic commision datas from self oject : commission_lines
				'account.invoice.commission' : (lambda self, cr, uid, ids, c={}: ids,['commission_lines','state','bill_ids'],21),
				# basic commision datas from sales contract : agent, payment to, percentage
				'sale.order.agent' : (_get_sale_order_agent, ['agent_id','invoice_partner_id','commission_percentage'], 24),
				# actual charge realisation, to compute amount fob : invoice charge and extra payment
				'account.invoice' : (_get_account_invoice_charge, ['state','invoice_line'], 23),
				'account.invoice.line': (_get_invoice_charge_line, ['price_unit','invoice_line_tax_id','quantity','invoice_related_id'], 25),
				'ext.transaksi' : (_get_ext_transaksi_charge, ['state','ext_line','tax_ext_line'], 23),
				'ext.transaksi.line' : (_get_ext_transaksi_charge_line, ['debit','credit','invoice_related_id'], 23),
				# actual rate invoice, to compute amount fob : invoice line and invoice tax line
				'account.invoice.line': (_get_commission_invoice_line, ['price_unit','invoice_line_tax_id','quantity','invoice_id'], 24),
				'account.invoice.tax': (_get_commission_invoice_tax, None, 24),
				# commision realisation : invoice charge created from bill passing
				'account.invoice' : (_get_account_invoice_chg, ['state'],23),
				# commision realisation payment : invoice move that have reconciled
				'account.move.line': (_get_invoice_from_line, None, 55),
				'account.move.reconcile': (_get_invoice_from_reconcile, None, 55),
			}, multi='comm_state'),

		"bpa_line_ids" : fields.one2many('ext.transaksi.line','commission_id','BPA Line'),
		"date_paid" : fields.date('Date Paid'),
		"date_knock_off" : fields.date('Date Knock Off'),
		"knock_off" : fields.boolean('Knock Off'),
		"state" : fields.function(_get_amount_status_comm, type='selection',method=True,string='Status', selection=[('knock_off','Knock Off'),('draft','Draft'),('provision','Provision'),('open','Open'),('paid','Paid')],
			store={
				# basic commision datas from self oject : commission_lines
				'account.invoice.commission' : (lambda self, cr, uid, ids, c={}: ids,['commission_lines','state','bill_ids'],21),
				# basic commision datas from sales contract : agent, payment to, percentage
				'sale.order.agent' : (_get_sale_order_agent, ['agent_id','invoice_partner_id','commission_percentage'], 24),
				# actual charge realisation, to compute amount fob : invoice charge and extra payment
				'account.invoice' : (_get_account_invoice_charge, ['state','invoice_line'], 23),
				'account.invoice.line': (_get_invoice_charge_line, ['price_unit','invoice_line_tax_id','quantity','invoice_related_id'], 25),
				'ext.transaksi' : (_get_ext_transaksi_charge, ['state','ext_line','tax_ext_line'], 23),
				'ext.transaksi.line' : (_get_ext_transaksi_charge_line, ['debit','credit','invoice_related_id'], 23),
				# actual rate invoice, to compute amount fob : invoice line and invoice tax line
				'account.invoice.line': (_get_commission_invoice_line, ['price_unit','invoice_line_tax_id','quantity','invoice_id'], 24),
				'account.invoice.tax': (_get_commission_invoice_tax, None, 24),
				# commision realisation : invoice charge created from bill passing
				'account.invoice' : (_get_account_invoice_chg, ['state'],23),
				# commision realisation payment : invoice move that have reconciled
				'account.move.line': (_get_invoice_from_line, None, 55),
				'account.move.reconcile': (_get_invoice_from_reconcile, None, 55),
			}, multi='comm_state'),
		"date_done" : fields.function(_get_amount_status_comm, type='date',method=True,string='Date done', 
			store={
				# basic commision datas from self oject : commission_lines
				'account.invoice.commission' : (lambda self, cr, uid, ids, c={}: ids,['commission_lines','state','bill_ids'],21),
				# basic commision datas from sales contract : agent, payment to, percentage
				'sale.order.agent' : (_get_sale_order_agent, ['agent_id','invoice_partner_id','commission_percentage'], 24),
				# actual charge realisation, to compute amount fob : invoice charge and extra payment
				'account.invoice' : (_get_account_invoice_charge, ['state','invoice_line'], 23),
				'account.invoice.line': (_get_invoice_charge_line, ['price_unit','invoice_line_tax_id','quantity','invoice_related_id'], 25),
				'ext.transaksi' : (_get_ext_transaksi_charge, ['state','ext_line','tax_ext_line'], 23),
				'ext.transaksi.line' : (_get_ext_transaksi_charge_line, ['debit','credit','invoice_related_id'], 23),
				# actual rate invoice, to compute amount fob : invoice line and invoice tax line
				'account.invoice.line': (_get_commission_invoice_line, ['price_unit','invoice_line_tax_id','quantity','invoice_id'], 24),
				'account.invoice.tax': (_get_commission_invoice_tax, None, 24),
				# commision realisation : invoice charge created from bill passing
				'account.invoice' : (_get_account_invoice_chg, ['state'],23),
				# commision realisation payment : invoice move that have reconciled
				'account.move.line': (_get_invoice_from_line, None, 55),
				'account.move.reconcile': (_get_invoice_from_reconcile, None, 55),
			}, multi='comm_state'),
	}

	def name_get(self, cr, uid, ids, context=None):
		if not ids:
			return []
		reads = self.read(cr, uid, ids, ['invoice_id'], context)
		res = []
		for record in reads:
			invoice_id = record['invoice_id'][0]
			invoice = self.pool.get('account.invoice').browse(cr, uid, invoice_id)
			
			name = invoice.internal_number and invoice.internal_number or invoice.number or str(record['id'])
			res.append((record['id'], name))
		return res

	def button_knock_off(self, cr, uid, ids, context=None):
		res = self.write(cr, uid, ids, {'knock_off': True, 'date_knock_off': time.strftime("%Y-%m-%d")})
		return True

	def action_create_bpa_provision(self, cr, uid, ids, currency_id=False, context=None):
		if context is None:
			context = {}

		bpa_obj = self.pool.get('account.bill.passing')
		bpa_line_obj = self.pool.get('account.bill.passing.line')
		charge_type_obj = self.pool.get('charge.type')
		partner_obj = self.pool.get('res.partner')
		current_bpa_id=False
		res = {}
		for outs_comm in self.browse(cr, uid, ids, context=context):
			# if not invoice.commission_ids:
			# 	continue
			if not outs_comm.invoice_id.actual_freight:
				continue

			date=context.get('bpa_date', False)
			if current_bpa_id:
				bpa_id=current_bpa_id
			else:
				bpa_id = bpa_obj.create(cr, uid, {
					'name' : '/',
					'journal_id': False,
					'currency_id': currency_id and currency_id or False,
					'date_entry': date,
					'due_date':context.get('due_date', False),
					}, context=context)
				res[outs_comm.id] = bpa_id
				current_bpa_id=bpa_id

			from_currency=outs_comm.invoice_id.currency_id.id
			to_currency=currency_id

			type_of_charge_ids=charge_type_obj.search(cr, uid, [('name','=','Sales Commission')])
			type_of_charge_id=False
			account_id=False
			if type_of_charge_ids:
				type_of_charge=charge_type_obj.browse(cr, uid, type_of_charge_ids)[0]
				type_of_charge_id=type_of_charge.id
				account_id=type_of_charge and type_of_charge.account_id.id or False

			context.update({'date':outs_comm.invoice_id.date_invoice or time.strftime('%Y-%m-%d')})

			amount = self.pool.get('res.currency').compute(cr, uid, from_currency, to_currency, (round(outs_comm.commission_amount,2)-outs_comm.amount_invoiced), context=context)

			bpa_line_id = bpa_line_obj.create(cr, uid, {
				'comm_provision_id':outs_comm.id,
				'type_of_charge': type_of_charge_id,
				'account_id':account_id,
				'invoice_related_id' : outs_comm.invoice_id.id,
				'name' : 'Sales Commission',
				'bill_id': bpa_id,
				'amount': amount,
				'partner_id': outs_comm.invoice_partner_id and outs_comm.invoice_partner_id.id or False,
				}, context=context)
			self.write(cr, uid, outs_comm.id, {'bill_prov_id':bpa_line_id})
		return res

	def action_create_bpa(self, cr, uid, ids, currency_id=False, context=None):
		if context is None:
			context = {}

		bpa_obj = self.pool.get('account.bill.passing')
		bpa_line_obj = self.pool.get('account.bill.passing.line')
		charge_type_obj = self.pool.get('charge.type')
		partner_obj = self.pool.get('res.partner')
		current_bpa_id=False
		res = {}
		for outs_comm in self.browse(cr, uid, ids, context=context):
			# if not invoice.commission_ids:
			# 	continue

			date=context.get('bpa_date', False)
			due_date=context.get('due_date', False)
			if current_bpa_id:
				bpa_id=current_bpa_id
			else:
				bpa_id = bpa_obj.create(cr, uid, {
					'name' : '/',
					'journal_id': False,
					'currency_id': currency_id and currency_id or False,
					'date_entry': date,
					'date_due':due_date,
					}, context=context)
				res[outs_comm.id] = bpa_id
				current_bpa_id=bpa_id

			from_currency=outs_comm.invoice_id.currency_id.id
			to_currency=currency_id

			type_of_charge_ids=charge_type_obj.search(cr, uid, [('name','=','Sales Commission')])
			type_of_charge_id=False
			account_id=False
			if type_of_charge_ids:
				type_of_charge=charge_type_obj.browse(cr, uid, type_of_charge_ids)[0]
				type_of_charge_id=type_of_charge.id
				account_id=type_of_charge and type_of_charge.account_id.id or False

			
			context_rate = context.copy()
			context_rate.update({'date':outs_comm.invoice_id.date_invoice or time.strftime('%Y-%m-%d')})
			if context.get('use_kmk_rate',False):
				context_rate.update({'date':context.get('date_supplier_invoice', context_rate.get('date',False))})
				amount = self.pool.get('res.currency').computerate(cr, uid, from_currency, to_currency, (round(outs_comm.commission_amount,2)-outs_comm.amount_invoiced), context=context_rate)
			else:
				amount = self.pool.get('res.currency').compute(cr, uid, from_currency, to_currency, (round(outs_comm.commission_amount,2)-outs_comm.amount_invoiced), context=context_rate)

			bpa_line_id = bpa_line_obj.create(cr, uid, {
				'comm_id':outs_comm.id,
				'type_of_charge': type_of_charge_id,
				'account_id':account_id,
				'invoice_related_id' : outs_comm.invoice_id.id,
				'name' : 'Sales Commission',
				'bill_id': bpa_id,
				'amount': amount,
				'partner_id': outs_comm.invoice_partner_id and outs_comm.invoice_partner_id.id or False,
				'invoice_id':outs_comm.invoice_prov_id and outs_comm.invoice_prov_id.id or False,
				'invoice_line_id':outs_comm.invoice_prov_line_id and outs_comm.invoice_prov_line_id.id or False,
				}, context=context)
		return res

class account_invoice(osv.osv):
	_inherit = "account.invoice"

	def _get_account_invoice_charge(self, cr, uid, ids, context=None):
		if not context:context={}
		res = []
		for inv in self.pool.get('account.invoice').browse(cr,uid,ids,context=context):
			if inv.invoice_line:
				for line in inv.invoice_line:
					if line.invoice_related_id:
						if line.invoice_related_id.id not in res:
							res.append(line.invoice_related_id.id)
		return res

	def _get_invoice_charge_line(self, cr, uid, ids, context=None):
		if not context:context={}
		res = []
		for line in self.pool.get('account.invoice.line').browse(cr,uid,ids,context=context):
			if line.invoice_related_id:
				if line.invoice_related_id.id not in res:
					res.append(line.invoice_related_id.id)
		return res

	def _get_ext_transaksi_charge(self,cr,uid,ids,context=None):
		if not context:context={}
		res = []

		for bpa in self.pool.get('ext.transaksi').browse(cr,uid,ids,context=context):
			if bpa.ext_line:
				for line in bpa.ext_line:
					if line.invoice_related_id:
						if line.invoice_related_id.id not in res:
							res.append(line.invoice_related_id.id)
		return res

	def _get_ext_transaksi_charge_line(self,cr,uid,ids,context=None):
		if not context:context={}
		res = []

		for line in self.pool.get('ext.transaksi.line').browse(cr,uid,ids,context=context):
			if line.invoice_related_id:
				if line.invoice_related_id.id not in res:
					res.append(line.invoice_related_id.id)
		return res

	def _get_invoice_line(self, cr, uid, ids, context=None):
		result = {}
		for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
			result[line.invoice_id.id] = True
		return result.keys()

	def _get_invoice_tax(self, cr, uid, ids, context=None):
		result = {}
		for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
			result[tax.invoice_id.id] = True
		return result.keys()

	def _get_charge_amount_all(self, cr, uid, ids, field_names, arg=None, context=None):
		if context is None:
			context = {}

		result = {}
		if not ids: return result
		for inv in self.browse(cr,uid,ids):
			result[inv.id] = {
				'amount_freight': 0.0,
				'amount_insurance': 0.0,
				'amount_fob': 0.0,
				'actual_freight': False,
			}
			total_freight=0.0
			total_insurance=0.0
			fob=0.0
			actual_freight = False
			# Charge Freight
			if inv.charge_invoice_ids and [x for x in inv.charge_invoice_ids if x.type_of_charge and x.type_of_charge.name=='Freight' and x.invoice_id.state in ['draft','proforma2','open','paid']]:
				# From current invoice freight
				for charge in inv.charge_invoice_ids:
					if charge.type_of_charge and charge.type_of_charge.name=='Freight':
						if charge.invoice_id.state in ['draft','proforma2','open','paid']:
							freight_invoice_currency=charge.invoice_id.currency_id.id
							invoice_currency=inv.currency_id.id
							context.update({'date':inv.date_invoice or time.strftime('%Y-%m-%d')})
							
							price = charge.price_unit * (1-(charge.discount or 0.0)/100.0) * charge.quantity
							amount_freight = self.pool.get('res.currency').compute(cr, uid, freight_invoice_currency, invoice_currency, price, context=context)
							
							total_freight += amount_freight
				actual_freight = total_freight>0 and True or False
			else:
				# From current master freight
				for picking in inv.picking_ids:
					context.update({'date':inv.date_invoice or time.strftime('%Y-%m-%d')})
					if picking.forwading_charge:
						forwading_currency=picking.forwading_charge.currency_id.id
						invoice_currency=inv.currency_id.id
						amount_freight = self.pool.get('res.currency').compute(cr, uid, forwading_currency, invoice_currency, picking.forwading_charge.cost or 0.0, context=context)
						total_freight += amount_freight
			# # Charge EMKL
			# if inv.charge_invoice_ids and [x for x in inv.charge_invoice_ids if x.type_of_charge and x.type_of_charge.name=='EMKL' and x.invoice_id.state in ['proforma2','open','paid']]:
		# 		# From current invoice EMKL
		# 		for charge in inv.charge_invoice_ids:
			# 		if charge.type_of_charge and charge.type_of_charge.name=='EMKL':
			# 			if charge.invoice_id.state in ['proforma2','open','paid']:
			# 				freight_invoice_currency=charge.invoice_id.currency_id.id
			# 				invoice_currency=inv.currency_id.id
			# 				context.update({'date':inv.date_invoice or time.strftime('%Y-%m-%d')})
			# 				amount_freight = self.pool.get('res.currency').compute(cr, uid, freight_invoice_currency, invoice_currency, (charge.price_subtotal), context=context)
			# 				total_freight += amount_freight
			# 	actual_freight = total_freight>0 and True or False
			# else:
		# 		# From current master EMKL
			# 	for picking in inv.picking_ids:
			# 		context.update({'date':inv.date_invoice or time.strftime('%Y-%m-%d')})
			# 		if picking.trucking_charge:
			# 			trucking_currency=picking.trucking_charge.currency_id.id
			# 			invoice_currency=inv.currency_id.id
			# 			amount_freight = self.pool.get('res.currency').compute(cr, uid, trucking_currency, invoice_currency, picking.trucking_charge.cost or 0.0, context=context)
			# 			total_freight += amount_freight

			# if inv.charge_bpa_ids and [x for x in inv.charge_bpa_ids if x.type_of_charge and x.type_of_charge.name=='Lift On Lift Off' and x.state in ['draft','posted']]:
		# 		for charge2 in inv.charge_bpa_ids:
			# 		if charge2.type_of_charge and charge2.type_of_charge.name == 'Lift On Lift Off':
			# 			if charge2.ext_transaksi_id and charge2.ext_transaksi_id.state in ['draft','posted']:
			# 				freight_invoice_currency=charge2.ext_transaksi_id.currency_id.id
			# 				invoice_currency=inv.currency_id.id
			# 				context.update({'date':inv.date_invoice or time.strftime('%Y-%m-%d')})
			# 				amount_freight = self.pool.get('res.currency').compute(cr, uid, freight_invoice_currency, invoice_currency, (charge2.debit-charge2.credit), context=context)
			# 				total_freight += amount_freight
			# else:
			# 	for picking in inv.picking_ids:
			# 		if picking.trucking_company and picking.container_size and picking.container_size.type:
			# 			context.update({'date':inv.date_invoice or time.strftime('%Y-%m-%d')})
			# 			total_lolo = 0.0
			# 			n = 0
			# 			for chg in picking.trucking_company.charge_ids:
			# 				if chg.is_lift_on_lift_off and chg.size_container and chg.size_container.name==picking.container_size.type.name:
			# 					lolo_currency=chg.currency_id.id
			# 					invoice_currency=inv.currency_id.id
			# 					total_lolo += self.pool.get('res.currency').compute(cr, uid, lolo_currency, invoice_currency, chg.cost, context=context)
			# 					n+=1
			# 			if n != 0:
			# 				total_freight += (total_lolo/n)


			# compute Insurance amount v1, from invoice charge
					# if charge.type_of_charge.name == 'Insurance':
					# 	if charge.invoice_id.state in ['draft','open','paid']:
					# 		insurence_invoice_currency=charge.invoice_id.currency_id.id
					# 		invoice_currency=inv.currency_id.id
					# 		context.update({'date':inv.date_invoice or time.strftime('%Y-%m-%d')})
					# 		amount_insurance = self.pool.get('res.currency').compute(cr, uid, insurence_invoice_currency, invoice_currency, charge.price_subtotal, context=context)
					# 		total_insurance += amount_insurance
			# compute Insurance amount v2, from insurance polis
			# insurance_doc = self.pool.get('insurance.polis').search(cr, uid, [('invoice_id','=',inv.id)])
			# for insurance in self.pool.get('insurance.polis').browse(cr, uid, insurance_doc or []):
			# 	insurence_invoice_currency=insurance.currency_id.id
			# 	invoice_currency=inv.currency_id.id
			# 	context.update({'date':inv.date_invoice or time.strftime('%Y-%m-%d')})
			# 	amount_insurance = self.pool.get('res.currency').compute(cr, uid, insurence_invoice_currency, invoice_currency, insurance.deductible_amount, context=context)
			# 	total_insurance += amount_insurance
			# compute Insurance amount v3, from insurance rate master
			incoterm=inv.incoterms or False
			if not incoterm and inv.sale_ids:
				for sale in inv.sale_ids:
					if sale.incoterm:
						incoterm = sale.incoterm
			if inv.sale_type and inv.sale_type=='export':
				insurance_type_pool = self.pool.get('insurance.type')
				insurance_rate = insurance_type_pool._get_rate(cr, uid, itype='sale',sale_type=inv.sale_type,incoterms=incoterm and incoterm.id or False,context=context.update({'date':inv.date_invoice or time.strftime('%Y-%m-%d')}))
				total_insurance+=(inv.amount_total+(inv.amount_total*10/100))*insurance_rate/100
				
			if incoterm:
				localdict = {'amount_invoice':inv.amount_total, 'total_freight':total_freight, 'total_insurance':total_insurance}
				exec incoterm.fob_compute in localdict
				fob = localdict['result']
			else:
				fob=inv.amount_total

			# update terbaru, fob = total - ocean freight
			fob = inv.amount_total - total_freight
			
			result[inv.id]['amount_insurance']=total_insurance
			result[inv.id]['amount_freight']=total_freight
			result[inv.id]['amount_fob']=fob
			result[inv.id]['actual_freight']=actual_freight
		return result

	def _get_commissions(self, cr, uid, ids, context=None):
		res = []
		for commission in self.pool.get('account.invoice.commission').browse(cr, uid, ids, context=context):
			if commission.invoice_id and commission.invoice_id.id not in res:
				res.append(commission.invoice_id.id)
		return res

	def _get_sale_order_agent(self, cr, uid, ids, context=None):
		res=[]
		for sale_order_agent in self.pool.get('sale.order.agent').browse(cr, uid, ids, context=context):
			if sale_order_agent.sale_id:
				if sale_order_agent.sale_id.invoice_ids:
					for invoice in sale_order_agent.sale_id.invoice_ids:
						if invoice.id not in res:
							res.append(invoice.id)
		return res

	def _get_invoice_commission(self,cr,uid,ids,context=None):
		if not context:context={}
		res = []
		for comm_line in self.pool.get('account.invoice.commission').browse(cr,uid,ids,context=context):
			if comm_line.invoice_id:
				if comm_line.invoice_id.id not in res:
					res.append(comm_line.invoice_id.id)
		return res

	def _get_insurance(self,cr,uid,ids,context=None):
		if not context:context={}
		res = []
		for insurance in self.pool.get('insurance.polis').browse(cr,uid,ids,context=context):
			if insurance.invoice_id:
				if insurance.invoice_id.id not in res:
					res.append(insurance.invoice_id.id)
		return res

	def _get_account_invoice_chg(self,cr,uid,ids,context=None):
		""" 
		This function is to get the account invoice of this commision outstanding that already valid
		or accrued and have had payable journal
		"""
		if not context:context={}
		res = []

		for inv in self.pool.get('account.invoice').browse(cr,uid,ids,context=context):
			if inv.bill_id:
				for bill_line in inv.bill_id.bill_lines:
					if bill_line.invoice_id == inv:
						inv_id = False
						if bill_line.comm_id and bill_line.comm_id.invoice_id:
							inv_id = bill_line.comm_id.invoice_id.id
						elif bill_line.comm_provision_id and bill_line.comm_provision_id.invoice_id:
							inv_id = bill_line.comm_provision_id.invoice_id.id
						if inv_id and inv_id not in res:
							res.append(inv_id)
		return res

	def _get_invoice_from_line(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		res = []
		move = {}
		for line in self.pool.get('account.move.line').browse(cr, uid, ids, context=context):
			if line.reconcile_partial_id:
				for line2 in line.reconcile_partial_id.line_partial_ids:
					move[line2.move_id.id] = True
			if line.reconcile_id:
				for line2 in line.reconcile_id.line_id:
					move[line2.move_id.id] = True
		invoice_ids = []
		if move:
			invoice_ids = self.pool.get('account.invoice').search(cr, uid, [('move_id','in',move.keys())], context=context)
			if invoice_ids:
				for inv in self.pool.get('account.invoice').browse(cr, uid, invoice_ids, context=context):
					if inv.bill_id:
						for bill_line in inv.bill_id.bill_lines:
							if bill_line.invoice_id == inv:
								inv_id = False
								if bill_line.comm_id and bill_line.comm_id.invoice_id:
									inv_id = bill_line.comm_id.invoice_id.id
								elif bill_line.comm_provision_id and bill_line.comm_provision_id.invoice_id:
									inv_id = bill_line.comm_provision_id.invoice_id.id
								if inv_id and inv_id not in res:
									res.append(inv_id)
		return res

	def _get_invoice_from_reconcile(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		res = []
		move = {}
		for r in self.pool.get('account.move.reconcile').browse(cr, uid, ids, context=context):
			for line in r.line_partial_ids:
				move[line.move_id.id] = True
			for line in r.line_id:
				move[line.move_id.id] = True

		invoice_ids = []
		if move:
			invoice_ids = self.pool.get('account.invoice').search(cr, uid, [('move_id','in',move.keys())], context=context)
			if invoice_ids:
				for inv in self.pool.get('account.invoice').browse(cr, uid, invoice_ids, context=context):
					if inv.bill_id:
						for bill_line in inv.bill_id.bill_lines:
							if bill_line.invoice_id == inv:
								inv_id = False
								if bill_line.comm_id and bill_line.comm_id.invoice_id:
									inv_id = bill_line.comm_id.invoice_id.id
								elif bill_line.comm_provision_id and bill_line.comm_provision_id.invoice_id:
									inv_id = bill_line.comm_provision_id.invoice_id.id
								if inv_id and inv_id not in res:
									res.append(inv_id)
		return res

	def _get_commission_amount_all(self, cr, uid, ids, field_names, arg=None, context=None):
		if context is None:
			context = {}
		result = {}
		if not ids: return result
		for inv in self.browse(cr,uid,ids):
			result[inv.id] = {
				'amount_commission': 0.0,
				'amount_commission_without_fob': 0.0,
				'amount_paid': 0.0,
				'commission_outstanding': 0.0
			}
			commission_amount=0.0
			commission_without_fob=0.0
			paid=0.0
			outstanding=0.0

			if inv.commission_ids:
				for commission in inv.commission_ids:
					if commission.commission_lines:
						commission_amount+=commission.commission_amount
						commission_without_fob+=commission.commission_amount_without_fob

						paid+=commission.amount_paid
						outstanding+=commission.amount_outstanding

			result[inv.id]['amount_commission'] = commission_amount
			result[inv.id]['amount_commission_without_fob'] = commission_without_fob
			result[inv.id]['amount_paid'] = paid
			if outstanding>=0:
				result[inv.id]['commission_outstanding'] = outstanding
		return result

	_columns = {
		"charge_invoice_ids" : fields.one2many('account.invoice.line','invoice_related_id','Invoice Charge',readonly=True),
		"charge_bpa_ids" : fields.one2many('ext.transaksi.line','invoice_related_id','Extra Transaction Charge',readonly=True),
		"amount_insurance" : fields.function(_get_charge_amount_all, type='float', method=True, string='Total Insurance Cost',digits_compute=dp.get_precision('Account'),
			store={
				# actual charge realisation, to compute amount fob : invoice charge and extra payment
				'account.invoice' : (_get_account_invoice_charge, ['state','invoice_line'], 20),
				'account.invoice.line': (_get_invoice_charge_line, ['price_unit','invoice_line_tax_id','quantity','invoice_related_id'], 22),
				'ext.transaksi' : (_get_ext_transaksi_charge, ['state','ext_line','tax_ext_line'], 20),
				'ext.transaksi.line' : (_get_ext_transaksi_charge_line, ['debit','credit','invoice_related_id'], 20),
				# actual rate invoice, to compute amount fob : invoice line and invoice tax line
				'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','invoice_id'], 21),
				'account.invoice.tax': (_get_invoice_tax, None, 21),
			},
			multi='all_for_fob'
			),
		"amount_freight" : fields.function(_get_charge_amount_all, type='float', method=True, string='Total Freight Cost',digits_compute=dp.get_precision('Account'),
			store={
				# actual charge realisation, to compute amount fob : invoice charge and extra payment
				'account.invoice' : (_get_account_invoice_charge, ['state','invoice_line'], 20),
				'account.invoice.line': (_get_invoice_charge_line, ['price_unit','invoice_line_tax_id','quantity','invoice_related_id'], 22),
				'ext.transaksi' : (_get_ext_transaksi_charge, ['state','ext_line','tax_ext_line'], 20),
				'ext.transaksi.line' : (_get_ext_transaksi_charge_line, ['debit','credit','invoice_related_id'], 20),
			},
			multi='all_for_fob'
			),
		"actual_freight" : fields.function(_get_charge_amount_all, type='boolean', method=True, string='Is Actual Freight',
			store={
				# actual charge realisation, to compute amount fob : invoice charge and extra payment
				'account.invoice' : (_get_account_invoice_charge, ['state','invoice_line'], 20),
				'account.invoice.line': (_get_invoice_charge_line, ['price_unit','invoice_line_tax_id','quantity','invoice_related_id'], 22),
				'ext.transaksi' : (_get_ext_transaksi_charge, ['state','ext_line','tax_ext_line'], 20),
				'ext.transaksi.line' : (_get_ext_transaksi_charge_line, ['debit','credit','invoice_related_id'], 20),
			},
			multi='all_for_fob'
			),
		"amount_fob" : fields.function(_get_charge_amount_all, type='float', method=True, string='Commission Base Amount',digits_compute=dp.get_precision('Account'),
			store={
				# actual charge realisation, to compute amount fob : invoice charge and extra payment
				'account.invoice' : (_get_account_invoice_charge, ['state','invoice_line'], 20),
				'account.invoice.line': (_get_invoice_charge_line, ['price_unit','invoice_line_tax_id','quantity','invoice_related_id'], 22),
				'ext.transaksi' : (_get_ext_transaksi_charge, ['state','ext_line','tax_ext_line'], 20),
				'ext.transaksi.line' : (_get_ext_transaksi_charge_line, ['debit','credit','invoice_related_id'], 20),
				# actual rate invoice, to compute amount fob : invoice line and invoice tax line
				'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','invoice_id'], 21),
				'account.invoice.tax': (_get_invoice_tax, None, 21),
			},
			multi='all_for_fob'
			),
		"commission_ids" : fields.one2many('account.invoice.commission','invoice_id','Agent`s Commission'),
		"amount_commission" : fields.function(_get_commission_amount_all, type='float', method=True, string='Total Commission',digits_compute=dp.get_precision('Account'),
			store={
				# basic commision datas from account invoice commission oject : commission_lines
				'account.invoice.commission' : (_get_commissions,['commission_lines','state'],22),
				# basic commision datas from sales contract : agent, payment to, percentage
				'sale.order.agent' : (_get_sale_order_agent, ['agent_id','invoice_partner_id','commission_percentage'], 25),
				'account.invoice' : (lambda self, cr, uid, ids, c={}: ids,['commission_ids','state'],19),
				# actual charge realisation, to compute amount fob : invoice charge and extra payment
				'account.invoice' : (_get_account_invoice_charge, ['state','invoice_line'], 24),
				'account.invoice.line': (_get_invoice_charge_line, ['price_unit','invoice_line_tax_id','quantity','invoice_related_id'], 26),
				'ext.transaksi' : (_get_ext_transaksi_charge, ['state','ext_line','tax_ext_line'], 24),
				'ext.transaksi.line' : (_get_ext_transaksi_charge_line, ['debit','credit','invoice_related_id'], 24),
				# actual rate invoice, to compute amount fob : invoice line and invoice tax line
				'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','invoice_id'], 24),
				'account.invoice.tax': (_get_invoice_tax, None, 24),
			},
			multi='all_commission'
			),
		"amount_commission_without_fob" : fields.function(_get_commission_amount_all, type='float', method=True, string='Total Commission Exclude Fob',digits_compute=dp.get_precision('Account'),
			store={
				# basic commision datas from account invoice commission oject : commission_lines
				'account.invoice.commission' : (_get_commissions,['commission_lines','state'],22),
				# basic commision datas from sales contract : agent, payment to, percentage
				'sale.order.agent' : (_get_sale_order_agent, ['agent_id','invoice_partner_id','commission_percentage'], 25),
				'account.invoice' : (lambda self, cr, uid, ids, c={}: ids,['commission_ids','state'],19),
				# actual charge realisation, to compute amount fob : invoice charge and extra payment
				'account.invoice' : (_get_account_invoice_charge, ['state','invoice_line'], 24),
				'account.invoice.line': (_get_invoice_charge_line, ['price_unit','invoice_line_tax_id','quantity','invoice_related_id'], 26),
				'ext.transaksi' : (_get_ext_transaksi_charge, ['state','ext_line','tax_ext_line'], 24),
				'ext.transaksi.line' : (_get_ext_transaksi_charge_line, ['debit','credit','invoice_related_id'], 24),
				# actual rate invoice, to compute amount fob : invoice line and invoice tax line
				'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','invoice_id'], 24),
				'account.invoice.tax': (_get_invoice_tax, None, 24),
			},
			multi='all_commission'
			),
		"amount_paid" : fields.function(_get_commission_amount_all, type='float', method=True, string='Amount Paid',digits_compute=dp.get_precision('Account'),
			store={
				# basic commision datas from account invoice commission oject : commission_lines
				'account.invoice.commission' : (_get_commissions,['commission_lines','state'],22),
				# basic commision datas from sales contract : agent, payment to, percentage
				'sale.order.agent' : (_get_sale_order_agent, ['agent_id','invoice_partner_id','commission_percentage'], 25),
				# actual charge realisation, to compute amount fob : invoice charge and extra payment
				'account.invoice' : (_get_account_invoice_charge, ['state','invoice_line'], 24),
				'account.invoice.line': (_get_invoice_charge_line, ['price_unit','invoice_line_tax_id','quantity','invoice_related_id'], 26),
				'ext.transaksi' : (_get_ext_transaksi_charge, ['state','ext_line','tax_ext_line'], 24),
				'ext.transaksi.line' : (_get_ext_transaksi_charge_line, ['debit','credit','invoice_related_id'], 24),
				# actual rate invoice, to compute amount fob : invoice line and invoice tax line
				'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','invoice_id'], 24),
				'account.invoice.tax': (_get_invoice_tax, None, 24),
				# commision realisation : invoice charge created from bill passing
				'account.invoice' : (_get_account_invoice_chg, ['state'],23),
				# commision realisation payment : invoice move that have reconciled
				'account.move.line': (_get_invoice_from_line, None, 55),
				'account.move.reconcile': (_get_invoice_from_reconcile, None, 55),
			},
			multi='all_commission'
			),
		"commission_outstanding" : fields.function(_get_commission_amount_all, type='float', method=True, string='Outstanding Commission',digits_compute=dp.get_precision('Account'),
			store={
				# basic commision datas from account invoice commission oject : commission_lines
				'account.invoice.commission' : (_get_commissions,['commission_lines','state'],22),
				# basic commision datas from sales contract : agent, payment to, percentage
				'sale.order.agent' : (_get_sale_order_agent, ['agent_id','invoice_partner_id','commission_percentage'], 25),
				'account.invoice' : (lambda self, cr, uid, ids, c={}: ids,['commission_ids','state'],19),
				# actual charge realisation, to compute amount fob : invoice charge and extra payment
				'account.invoice' : (_get_account_invoice_charge, ['state','invoice_line'], 24),
				'account.invoice.line': (_get_invoice_charge_line, ['price_unit','invoice_line_tax_id','quantity','invoice_related_id'], 26),
				'ext.transaksi' : (_get_ext_transaksi_charge, ['state','ext_line','tax_ext_line'], 24),
				'ext.transaksi.line' : (_get_ext_transaksi_charge_line, ['debit','credit','invoice_related_id'], 24),
				# actual rate invoice, to compute amount fob : invoice line and invoice tax line
				'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','invoice_id'], 24),
				'account.invoice.tax': (_get_invoice_tax, None, 24),
				# commision realisation : invoice charge created from bill passing
				'account.invoice' : (_get_account_invoice_chg, ['state'],23),
				# commision realisation payment : invoice move that have reconciled
				'account.move.line': (_get_invoice_from_line, None, 55),
				'account.move.reconcile': (_get_invoice_from_reconcile, None, 55),
			},
			multi='all_commission'
			),
		"bill_id" : fields.many2one('account.bill.passing','Bill Passing'),
	}

	def action_commission_open(self, cr, uid, ids, context=None):
		account_invoice_commission_pooler=self.pool.get('account.invoice.commission')
		account_invoice_commission_line_pooler=self.pool.get('account.invoice.commission.line')
		sale_order_agent_pooler = self.pool.get('sale.order.agent')

		if context is None:
			context = {}

		for obj_inv in self.browse(cr, uid, ids, context=context):
			all_sale_line_objs = []
			for line in obj_inv.invoice_line:
				if line.move_line_ids:
					for move in line.move_line_ids:
						if move.sale_line_id and move.sale_line_id not in all_sale_line_objs:
							all_sale_line_objs.append(move.sale_line_id)

			if all_sale_line_objs:
				# ADD NEW ACCOUNT COMMISSION LINE OR ACCOUNT COMMISSION IF ITS NOT IN COMMISSION IDS OF INVOICE
				aics = [] # account.invoice.commission
				aicls = [] # account.invoice.commission.line
				curr_soa_objs = []
				all_soa_ids = sale_order_agent_pooler.search(cr, uid, [('sale_line_id','in',[x.id for x in all_sale_line_objs])])
				all_soa_objs = []
				if all_soa_ids:
					all_soa_objs = sale_order_agent_pooler.browse(cr, uid, all_soa_ids)
				if obj_inv.commission_ids:
					aics = obj_inv.commission_ids
					aicls = [y for x in obj_inv.commission_ids if x.commission_lines for y in x.commission_lines]
					if aicls:
						curr_soa_objs = [x.sale_order_agent_id for x in aicls if x.sale_order_agent_id]

				to_add_soa_objs = all_soa_objs
				if curr_soa_objs:
					to_add_soa_objs = [x for x in to_add_soa_objs if x not in curr_soa_objs]

				curr_commissions = {}
				if aics:
					for comm in aics:
						curr_commissions.update({comm.invoice_partner_id.id : comm.id})
				
				if to_add_soa_objs:
					soas = to_add_soa_objs #sale.order.agent
					for soa in soas:
						if soa.invoice_partner_id.id in curr_commissions.keys():
							# add new commission line to related comm
							account_invoice_commission_line_pooler.create(cr, uid, {
								"commission_id" : curr_commissions[soa.invoice_partner_id.id],
								"sale_order_agent_id" : soa.id,
							})
						else:
							new_id = account_invoice_commission_pooler.create(cr, uid, {
								'invoice_id' : obj_inv.id,
								'commission_lines' : [(0,0,{"sale_order_agent_id" : soa.id})],
								})
							curr_commissions.update({soa.invoice_partner_id.id : new_id})
				
				# UPDATE ACCOUNT COMMISSION LINE OR ACCOUNT COMMISSION
				if aics:
					for comm in aics:
						for line in comm.commission_lines:
							if comm.invoice_partner_id and line.invoice_partner_id and comm.invoice_partner_id.id!=line.invoice_partner_id.id:
								if line.invoice_partner_id.id in curr_commissions.keys():
									account_invoice_commission_line_pooler.write(cr, uid, line.id, {'commission_id':curr_commissions[line.invoice_partner_id.id]})
								else:
									new_id = account_invoice_commission_pooler.create(cr, uid, {
										'invoice_id' : obj_inv.id,
										'commission_lines' : [(4,line.id)],
										})
									curr_commissions.update({soa.invoice_partner_id.id : new_id})
					# run trigger
					for aic in aics:
						account_invoice_commission_pooler.write(cr, uid, aic.id, {'commission_lines':[]})

		return True

	# def action_bpa_create(self, cr, uid, ids, currency_id=False, context=None):
	# 	""" Creates bpa based on the invoice selected for commission.
	# 	@param currency_id: Id of journal
	# 	@return: Ids of created bpa for the invoice
	# 	"""
	# 	if context is None:
	# 		context = {}

	# 	bpa_obj = self.pool.get('ext.transaksi')
	# 	bpa_line_obj = self.pool.get('ext.transaksi.line')
	# 	charge_type_obj = self.pool.get('charge.type')
	# 	partner_obj = self.pool.get('res.partner')
	# 	current_bpa_id=False
	# 	res = {}
	# 	for invoice in self.browse(cr, uid, ids, context=context):
	# 		if not invoice.commission_ids:
	# 			continue

	# 		date=context.get('bpa_date', False)
	# 		if current_bpa_id:
	# 			bpa_id=current_bpa_id
	# 		else:
	# 			bpa_id = bpa_obj.create(cr, uid, {
	# 				'name' : '/',
	# 				'journal_id': journal_id and journal_id or False,
	# 				'ref': '',
	# 				'request_date': date,
	# 				'due_date':context.get('due_date', False),
	# 				}, context=context)
	# 			res[invoice.id] = bpa_id
	# 			current_bpa_id=bpa_id

	# 		from_currency=invoice.currency_id.id
	# 		journal = self.pool.get('account.journal').browse(cr, uid, journal_id)
	# 		if journal:
	# 			to_currency=journal.currency.id or invoice.company_id.currency_id.id

	# 		for commission in invoice.commission_ids:
	# 			if commission.commission_amount == 0.0:
	# 				continue
				
	# 			paid_amount=0.0
	# 			if commission.bpa_line_ids:
	# 				for payment in commission.bpa_line_ids:
	# 					if payment.ext_transaksi_id.state=='posted':
	# 						# compute debit amount on BPA into invoice related base currency
	# 						ext_transaksi_currency=payment.ext_transaksi_id.journal_id.currency.id or invoice.company_id.currency_id.id
	# 						invoice_currency=from_currency
	# 						context.update({'date':invoice.date_invoice or time.strftime('%Y-%m-%d')})
	# 						bpa_line_debit_amount = self.pool.get('res.currency').compute(cr, uid, ext_transaksi_currency, invoice_currency, payment.debit, context=context)
							
	# 						paid_amount+=bpa_line_debit_amount
	# 			if paid_amount>=commission.commission_amount:
	# 				continue

	# 			type_of_charge_ids=charge_type_obj.search(cr, uid, [('name','=','Sales Commission')])
	# 			type_of_charge_id=False
	# 			account_id=False
	# 			if type_of_charge_ids:
	# 				type_of_charge=charge_type_obj.browse(cr, uid, type_of_charge_ids)[0]
	# 				type_of_charge_id=type_of_charge.id
	# 				account_id=type_of_charge and type_of_charge.account_id.id or False


	# 			context.update({'date':invoice.date_invoice or time.strftime('%Y-%m-%d')})
	# 			debit_amount = self.pool.get('res.currency').compute(cr, uid, from_currency, to_currency, (commission.commission_amount-paid_amount), context=context)

	# 			bpa_line_id = bpa_line_obj.create(cr, uid, {
	# 				'commission_id':commission.id,
	# 				'type_of_charge': type_of_charge_id,
	# 				'account_id':account_id,
	# 				'invoice_related_id' : invoice.id,
	# 				'name' : 'Sales Commission',
	#					'ext_transaksi_id': bpa_id,
	# 				'debit': debit_amount,
	# 				'partner_id': commission.invoice_partner_id and commission.invoice_partner_id.id or False,
	# 				}, context=context)
	# 	return res
account_invoice()

class account_invoice_line(osv.osv):
	def _get_amount_tax(self, cr, uid, ids, prop, unknow_none, unknow_dict):
		res = {}
		tax_obj = self.pool.get('account.tax')
		cur_obj = self.pool.get('res.currency')
		for line in self.browse(cr, uid, ids):
			# price = line.price_unit * (1-(line.discount or 0.0)/100.0)
			disc = self.pool.get('price.discount').compute_discounts(cr,uid,[x.id for x in line.discount_ids],line.price_unit,line.quantity,context={})
			price_after = disc.get('price_after',line.price_unit)
			taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price_after, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
			res[line.id] = taxes['total_included'] - taxes['total']
			if line.invoice_id:
				cur = line.invoice_id.currency_id
				res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
		return res

	def _get_amount_tax_vat(self, cr, uid, ids, prop, unknow_none, unknow_dict):
		res = {}
		tax_obj = self.pool.get('account.tax')
		cur_obj = self.pool.get('res.currency')
		for line in self.browse(cr, uid, ids):
			price = line.price_unit * (1-(line.discount or 0.0)/100.0)

			taxes = tax_obj.compute_all(cr, uid, [tax for tax in line.invoice_line_tax_id if tax.tax_sign>0], price, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
			res[line.id] = taxes['total_included'] - taxes['total']
			if line.invoice_id:
				cur = line.invoice_id.currency_id
				res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
		return res

	_inherit = "account.invoice.line"
	_columns = {
		'tax_amount':fields.function(_get_amount_tax, type='float', method=True, string='Tax Amount', digits_compute=dp.get_precision('Account'),store={
				'account.invoice.line':(lambda self,cr,uid,ids,context={}:ids,['price_unit','quantity','invoice_line_tax_id'],10),
			}),
		'vat_non_pph_amt':fields.function(_get_amount_tax_vat, type='float', method=True, string='VAT Amount only', digits_compute=dp.get_precision('Account'),store={
				'account.invoice.line':(lambda self,cr,uid,ids,context={}:ids,['price_unit','quantity','invoice_line_tax_id'],10),
			}),
	}