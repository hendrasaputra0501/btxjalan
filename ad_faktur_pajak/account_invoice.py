from mx import DateTime
from lxml import etree

from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import time
import urllib3
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class account_tax_code(osv.osv):
	_inherit = "account.tax.code"
	def _sum(self, cr, uid, ids, name, args, context, where ='', where_params=()):
		parent_ids = tuple(self.search(cr, uid, [('parent_id', 'child_of', ids)]))
		if context.get('based_on', 'invoices') == 'payments':
			cr.execute('SELECT line.tax_code_id, sum(coalesce(line.tax_amount,0.0)) \
					FROM account_move_line AS line, \
						account_move AS move \
						LEFT JOIN account_invoice invoice ON \
							(invoice.move_id = move.id) \
					WHERE line.tax_code_id IN %s '+where+' \
						AND move.id = line.move_id \
						AND ((invoice.state = \'paid\') \
							OR (invoice.id IS NULL)) \
							GROUP BY line.tax_code_id',
								(parent_ids,) + where_params)
		else:
			cr.execute('SELECT line.tax_code_id, sum(coalesce(line.tax_amount,0.0)) \
					FROM account_move_line AS line, \
					account_move AS move \
					WHERE line.tax_code_id IN %s '+where+' \
					AND move.id = line.move_id \
					GROUP BY line.tax_code_id',
					   (parent_ids,) + where_params)
		# print "parent_ssssssssss",parent_ids,where,where_params
		res=dict(cr.fetchall())
		obj_precision = self.pool.get('decimal.precision')
		res2 = {}
		for record in self.browse(cr, uid, ids, context=context):
			def _rec_get(record):
				amount = res.get(record.id, 0.0)
				for rec in record.child_ids:
					#print "rec.id--------------",rec.id,rec.name
					amount += _rec_get(rec) * rec.sign
				return amount
			res2[record.id] = round(_rec_get(record), obj_precision.precision_get(cr, uid, 'Account'))
		return res2


class account_invoice_tax(osv.osv):
	_inherit = "account.invoice.tax"

	def move_line_get(self, cr, uid, invoice_id):
		res = []
		cr.execute('SELECT * FROM account_invoice_tax WHERE invoice_id=%s', (invoice_id,))
		for t in cr.dictfetchall():
			if not t['amount'] \
					and not t['tax_code_id'] \
					and not t['tax_amount']:
				continue
			res.append({
				'type':'tax',
				'name':t['name'],
				'price_unit': t['amount'],
				'quantity': 1,
				'price': t['amount'] or 0.0,
				'account_id': t['account_id'],
				'tax_code_id': t['tax_code_id'],
				'tax_amount': t['tax_amount'],
				'base_amount': t['base_amount'],
				'amount': t['amount'],
				'base': t['base'],
				'account_analytic_id': t['account_analytic_id'],
			})
		return res
	


class account_invoice(osv.osv):
	_inherit="account.invoice"
	
	# def create(self, cr, uid, vals, context=None):
	# 	if 'nomor_faktur_id' in vals:
	# 		self.pool.get('nomor.faktur.pajak').write(cr, uid, vals['nomor_faktur_id'], {'status':'1'})
	# 	return super(account_invoice, self).create(cr, uid, vals, context=context)
	
	def onchange_partner_id(self, cr, uid, ids, type, partner_id,\
			date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
		partner_payment_term = False
		acc_id = False
		bank_id = False
		fiscal_position = False
		
		opt = [('uid', str(uid))]
		if partner_id:

			opt.insert(0, ('id', partner_id))
			p = self.pool.get('res.partner').browse(cr, uid, partner_id)
			if company_id:
				if (p.property_account_receivable.company_id and (p.property_account_receivable.company_id.id != company_id)) and (p.property_account_payable.company_id and (p.property_account_payable.company_id.id != company_id)):
					property_obj = self.pool.get('ir.property')
					rec_pro_id = property_obj.search(cr,uid,[('name','=','property_account_receivable'),('res_id','=','res.partner,'+str(partner_id)+''),('company_id','=',company_id)])
					pay_pro_id = property_obj.search(cr,uid,[('name','=','property_account_payable'),('res_id','=','res.partner,'+str(partner_id)+''),('company_id','=',company_id)])
					if not rec_pro_id:
						rec_pro_id = property_obj.search(cr,uid,[('name','=','property_account_receivable'),('company_id','=',company_id)])
					if not pay_pro_id:
						pay_pro_id = property_obj.search(cr,uid,[('name','=','property_account_payable'),('company_id','=',company_id)])
					rec_line_data = property_obj.read(cr,uid,rec_pro_id,['name','value_reference','res_id'])
					pay_line_data = property_obj.read(cr,uid,pay_pro_id,['name','value_reference','res_id'])
					rec_res_id = rec_line_data and rec_line_data[0].get('value_reference',False) and int(rec_line_data[0]['value_reference'].split(',')[1]) or False
					pay_res_id = pay_line_data and pay_line_data[0].get('value_reference',False) and int(pay_line_data[0]['value_reference'].split(',')[1]) or False
					if not rec_res_id and not pay_res_id:
						raise osv.except_osv(_('Configuration Error!'),
							_('Cannot find a chart of accounts for this company, you should create one.'))
					account_obj = self.pool.get('account.account')
					rec_obj_acc = account_obj.browse(cr, uid, [rec_res_id])
					pay_obj_acc = account_obj.browse(cr, uid, [pay_res_id])
					p.property_account_receivable = rec_obj_acc[0]
					p.property_account_payable = pay_obj_acc[0]

			if type in ('out_invoice', 'out_refund'):
				acc_id = p.property_account_receivable.id
				partner_payment_term = p.property_payment_term and p.property_payment_term.id or False
			else:
				acc_id = p.property_account_payable.id
				partner_payment_term = p.property_supplier_payment_term and p.property_supplier_payment_term.id or False
			fiscal_position = p.property_account_position and p.property_account_position.id or False
			if p.bank_ids:
				bank_id = p.bank_ids[0].id
		faktur = "" 
		if partner_id:
			p = self.pool.get('res.partner').browse(cr, uid, partner_id)		
			# print "p-----------------------------------------",p,p.npwp
			if p.npwp and len(p.npwp)==20:
				faktur = "%s%s." % (p.npwp and len(p.npwp)==20 and p.npwp[0:3],p.npwp and len(p.npwp)==20 and p.npwp[3:1])

		result = {'value': {
			'account_id': acc_id,
			'nomor_faktur_company': faktur,
			'payment_term': partner_payment_term,
			'fiscal_position': fiscal_position
			}
		}

		if type in ('in_invoice', 'in_refund'):
			result['value']['partner_bank_id'] = bank_id

		if payment_term != partner_payment_term:
			if partner_payment_term:
				to_update = self.onchange_payment_term_date_invoice(
					cr, uid, ids, partner_payment_term, date_invoice)
				result['value'].update(to_update['value'])
			else:
				result['value']['date_due'] = False

		if partner_bank_id != bank_id:
			to_update = self.onchange_partner_bank(cr, uid, ids, bank_id)
			result['value'].update(to_update['value'])
		return result
	
	_columns = {
			'phone'				 : fields.related('partner_id', 'mobile', type='char', string='Phone', readonly=True),
			"separate_tax"		  :fields.boolean('Separate AR/AP TAX ?'),
			"use_kmk_ar_ap"		 :fields.boolean("Use KMK for AR/AP?",help="Check this box if you want to apply KMK Rate for AR/AP"),
			'nomor_faktur_id'	   : fields.many2one('nomor.faktur.pajak', string='Nomor Faktur Pajak'),
			'kode_transaksi_faktur_pajak'  : fields.char("Kode Transaksi Faktur Pajak", size=3),
			'company_currency'	  :fields.related('company_id','currency_id',type="many2one",relation="res.currency",string="Company Currency"),
			'currency_tax_id'	   : fields.many2one('res.currency', string='Currency Tax',help="If using IDR, then tax rate will be using KMK Rate, \
				if it is using same currency with Company Currency, then the tax rate will be using the same rate with Company Currency rate"),	 
			'tax_date'			  :fields.date("Tax Date"),
			'faktur_pajak_date_entry' :fields.date("Entry Date of Faktur Pajak"),
			'fp_harga_jual'	: fields.boolean('Harga Jual'),
			'fp_penggantian'	: fields.boolean('Penggantian'),
			'fp_uang_muka'	: fields.boolean('Uang Muka'),
			'fp_termin'	: fields.boolean('Termin'),
			'authorized_by' : fields.many2one('hr.employee','Authorized By'),
			'job_position_id' : fields.many2one('hr.job','Job Position'),
			# 'faktur_pajak_lines' : fields.one2many('account.invoice.faktur.pajak','invoice_id','Faktur Pajak Lines'),
			'return_source_doc' : fields.char('Return Source Doc.'),
			'qr_urls' :  fields.text("Efaktur URLs"),
			'faktur_pajak_lines' : fields.one2many('efaktur.head','related_invoice_id','Faktur Pajak Lines'),
	}

	def write(self, cr, uid, ids, vals, context=None):
		if not context:
			context={}
		if vals.get('nomor_faktur_id',False):
			faktur = self.pool.get('nomor.faktur.pajak').browse(cr, uid, vals['nomor_faktur_id'])
			if faktur.account_invoice_ids:
				inv_type = list(set([x.type for x in faktur.account_invoice_ids]))
				for inv in self.browse(cr, uid, ids, context=context):
					if inv.type in inv_type:
						raise osv.except_osv(_('Faktur Pajak Error!'), _('Faktur Pajak %s is already used by other Invoice. Please select another one.'%str(faktur.name)))
		res =super(account_invoice,self).write(cr,uid,ids,vals,context)
		return res


	def onchange_authorized_by(self, cr, uid, ids, authorized_by, context=None):
		if context is None: context = {}
		res = {'job_position_id':False}
		if authorized_by:
			employee = self.pool.get('hr.employee').browse(cr, uid, authorized_by, context=context)
			if employee and employee.job_id:
				res['job_position_id']=employee.job_id.id
		return {'value':res}

	def _get_separate_tax(self,cr,uid,context=None):
		if not context:context={}
		separate_tax = False
		if context.get('type','out_invoice')=='out_invoice':
			separate_tax = False
		else:
			separate_tax = True
		return separate_tax

	def _get_currency(self,cr,uid,context=None):
		if not context:context={}
		xx = self.pool.get('res.currency').search(cr,uid,[('name','=','IDR')],context=context)
		#print "----x---x-x-x",xx
		return self.pool.get('res.currency').search(cr,uid,[('name','=','IDR')],context=context)[0]

	
	def _get_nomor(self, cr, uid, partner_id=False, context=None):
		if context is None:
			context = {}
		user = self.pool.get('res.partner').browse(cr,uid,partner_id,context=context)
		faktur = ""
		if user != False and user.npwp:
			faktur = "%s%s." % (user.npwp[0:3], user.npwp[3:1])
		return faktur 
		
	_defaults = {
			'currency_tax_id':_get_currency,
			'separate_tax':_get_separate_tax,
			'use_kmk_ar_ap':lambda self,cr,uid,context:False,
			# "tax_date":lambda *a:date.today().strftime('%Y-%m-%d'),
			'fp_harga_jual':lambda self,cr,uid,context:True,
	}

	def get_tax_data(self, cr, uid, ids, context=None):
		if not context:context={}
		ulib3 = urllib3.PoolManager()
		efaktur_head_pool = self.pool.get('efaktur.head')
		for invoice in self.browse(cr, uid, ids, context=context):
			npwpcompany = invoice.company_id.npwp.replace(".","").replace("-","")
			urls=invoice.qr_urls
			
			urlspot=[]
			for url in urls.split("http://"):
				if url and url!='' and url not in ("\n","\t","\r"):
					href="http://"+url
					head_ids = efaktur_head_pool.search(cr, uid, [('url','=',href.strip())])
					if not head_ids:
						urlspot.append(href.strip())
					if head_ids:
						for efaktur in efaktur_head_pool.browse(cr, uid, head_ids):
							if efaktur.related_invoice_id and efaktur.related_invoice_id.id!=invoice.id:
								raise osv.except_osv(_('Error Validation'), _("Factur no. %s is already linked with invoice no. %s"%(efaktur.nomorFaktur, efaktur.related_invoice_id.internal_number)))
							else:
								efaktur_head_pool.write(cr, uid, efaktur.id, {'related_invoice_id':invoice.id})

			for link in list(set(urlspot)):
				try:
					res = ulib3.request('GET', link)
					if res.status==200 and res.data:
						tree = etree.fromstring(res.data)
						efaktur_head={}
						detailtrans = []
						for subtree1 in tree:
							if subtree1.tag!='detailTransaksi':
								if subtree1.tag=="tanggalFaktur":
									dts=datetime.strptime(subtree1.text,"%d/%m/%Y").strftime('%Y-%m-%d')
									efaktur_head.update({subtree1.tag:dts})
								else:
									efaktur_head.update({subtree1.tag:subtree1.text})
							else:
								dumpy = {}
								for detail in subtree1.getchildren():
									dumpy.update({detail.tag:detail.text})
									if detail.tag=='ppnbm':
										detailtrans.append((0,0,dumpy))
										dumpy={}
							
						efaktur_head.update({
							'related_invoice_id':invoice.id,
							'company_id':invoice.company_id.id,
							'url': link,
							'type': npwpcompany == efaktur_head.get('npwpPenjual',False) and 'out' or 'in',
							"efaktur_lines":detailtrans
							})
						self.pool.get('efaktur.head').create(cr, uid, efaktur_head, context=context)
						# self.pool.get('efaktur.batch').write(cr,uid,batch.id,{'batch_lines':[]})
				except:
					raise osv.except_osv(_('Error Connecting to Server'), _("The connection to http://svc.efaktur.pajak.go.id/ can not be established."))
		return True
	
	def compute_invoice_totals(self, cr, uid, inv, company_currency, ref, invoice_move_lines, context=None):
		if context is None:
			context={}
		total = 0
		total_currency = 0
		cur_obj = self.pool.get('res.currency')
		tax_currency = inv.currency_tax_id and inv.currency_tax_id.id or company_currency
		tax_base_currency = inv.company_id and inv.company_id.tax_base_currency and inv.company_id.tax_base_currency.id or tax_currency
		
		# penanda menggunakan agar rate kmk disetiap account receiveble dan atau account tax
		is_kmk_tax = inv.company_id and inv.company_id.tax_base_currency and (inv.company_id.tax_base_currency.id == inv.currency_tax_id.id)

		context_rate = context.copy()

		context_rate.update({'date':inv.tax_date or inv.date_invoice or time.strftime('%Y-%m-%d'),'trans_currency':inv.currency_id and inv.currency_id.id or False})
		for i in invoice_move_lines:
			if inv.currency_id.id != company_currency:
				context.update({'date': inv.date_invoice or time.strftime('%Y-%m-%d')})
				i['currency_id'] = inv.currency_id.id
				i['amount_currency'] = i['price']

				if i['type'] == 'tax':
					if is_kmk_tax:
						context_rate.update({'reverse':False})
						# i['amount_currency'] = cur_obj.computerate(cr, uid, inv.currency_id.id, tax_base_currency, i['price'], context=context_rate)
						i['amount_currency'] = round(round(i['tax_amount']/i['base_amount'],2)*cur_obj.computerate(cr, uid, inv.currency_id.id, tax_base_currency, i['base'], context=context_rate),0)
						if inv.currency_id.id!=inv.company_id.tax_base_currency.id:
							context_rate.update({'reverse':True})
							i['price'] = cur_obj.compute(cr, uid, inv.currency_id.id ,company_currency, i['price'],round=True, context=context)
						else:
							i['amount_currency'] = i['price']
							i['currency_id'] = inv.currency_id.id
							context_rate.update({'reverse':True})
							i['price'] = cur_obj.computerate(cr, uid, inv.currency_id.id ,company_currency, i['amount_currency'],round=True, context=context_rate)
						i['currency_id'] = tax_currency
						i['tax_amount'] = i['price'] 
					else:
						i['price'] = cur_obj.compute(cr, uid, inv.currency_id.id,
								company_currency, i['price'],
								context=context)
						# i['currency_id'] = inv.currency_id and inv.currency_id.id or False
				else:	
					# if not inv.use_kmk_ar_ap:
					# 	i['price'] = cur_obj.compute(cr, uid, inv.currency_id.id,
					# 			company_currency, i['price'],
					# 			context=context)
					# else:
					# 	context_rate.update({'reverse':False})
					# 	i['amount_currency'] = cur_obj.computerate(cr, uid, inv.currency_id.id, tax_base_currency, i['price'], context=context_rate)
					# 	context_rate.update({'reverse':True})
					# 	i['price'] = cur_obj.computerate(cr, uid, tax_base_currency, company_currency, i['amount_currency'], context=context_rate)
					# 	i['tax_amount'] = i['price']
					if is_kmk_tax and inv.use_kmk_ar_ap:
						context_rate.update({'reverse':False})
						i['amount_currency'] = cur_obj.computerate(cr, uid, inv.currency_id.id, tax_base_currency, i['price'], context=context_rate)
						context_rate.update({'reverse':True})
						i['price'] = cur_obj.computerate(cr, uid, tax_base_currency, company_currency, i['amount_currency'],round=True, context=context_rate)
						i['tax_amount'] = i['price']
					else:
						i['price'] = cur_obj.compute(cr, uid, inv.currency_id.id,
							company_currency, i['price'],round=True,
							context=context)
						# print "#################################",i['price']
			else:
				i['amount_currency'] = False
				i['currency_id'] = False
				i['ref'] = ref
				if i['type'] == 'tax':
					if is_kmk_tax:
						# i['amount_currency'] = cur_obj.computerate(cr, uid, inv.currency_id.id, tax_base_currency, i['price'], context=context_rate)
						i['amount_currency'] = round(round(i['tax_amount']/i['base_amount'],2)*cur_obj.computerate(cr, uid, inv.currency_id.id, tax_base_currency, i['base'], context=context_rate),0)
						i['currency_id'] = tax_base_currency
				elif i['type'] != 'tax' and inv.use_kmk_ar_ap:
				# 	if inv.currency_tax_id.id != company_currency  and inv.use_kmk_ar_ap:
				# 		i['amount_currency'] = cur_obj.computerate(cr, uid, inv.currency_id.id, tax_base_currency, i['price'], context=context_rate)
				# 		i['currency_id']=t1ax_base_currency or False
				# 	elif inv.currency_tax_id.id == company_currency and inv.use_kmk_ar_ap:
				# 		i['amount_currency'] = cur_obj.computerate(cr, uid, inv.currency_id.id, tax_base_currency, i['price'], context=context_rate)
				# 		i['currency_id']=tax_base_currency or False
					if is_kmk_tax:
						i['amount_currency'] = cur_obj.computerate(cr, uid, inv.currency_id.id, tax_base_currency, i['price'], context=context_rate)
						i['currency_id']=tax_base_currency or False


			if inv.type in ('out_invoice','in_refund'):
				total += i['price']
				total_currency += i['amount_currency'] or i['price']
				i['price'] = - i['price']
			else:
				total -= i['price']
				total_currency -= i['amount_currency'] or i['price']
		# print "total===============",total
		return total, total_currency, invoice_move_lines

	def finalize_invoice_move_lines(self, cr, uid, invoice_browse, move_lines):
		"""finalize_invoice_move_lines(cr, uid, invoice, move_lines) -> move_lines
		Hook method to be overridden in additional modules to verify and possibly alter the
		move lines to be created by an invoice, for special cases.
		:param invoice_browse: browsable record of the invoice that is generating the move lines
		:param move_lines: list of dictionaries with the account.move.lines (as for create())
		:return: the (possibly updated) final move_lines to create for this invoice
		"""
		res = super(account_invoice,self).finalize_invoice_move_lines(cr, uid, invoice_browse, move_lines)
		moves = False
		if invoice_browse.separate_tax:
			account_pool = self.pool.get('account.account')
			cur_obj = self.pool.get('res.currency')
			account_ids = [x[2]['account_id'] for x in res]
			rec_payable_id = account_pool.search(cr,uid,[('id','in',account_ids),('type','in',('payable','receivable'))])
		
			if not rec_payable_id and invoice_browse.type =='out_invoice':
				raise osv.except_osv(_('No Receivable Account Defined!'), _('There is no Receivable Account Defined on this transaction, please check your account configuration.'))
			elif not rec_payable_id and invoice_browse.type =='in_invoice':
				raise osv.except_osv(_('No Payable Account Defined!'), _('There is no Payable Account Defined on this transaction, please check your account configuration.'))
			moves =[]
			moves_ar_ap = False
			total_tax_amt_currency=0.0
			total_trans_amt_currency = 0.0
			total_trans_amt_currency2 = 0.0
			total_tax = 0.0
			all_taxes = self.pool.get('account.tax').search(cr,uid,[])
			codes = [t.tax_code_id and t.tax_code_id.id for t in self.pool.get('account.tax').browse(cr,uid,all_taxes)] + [t.ref_tax_code_id and t.ref_tax_code_id.id for t in self.pool.get('account.tax').browse(cr,uid,all_taxes)]
			codes = list(set(codes))
			base_codes = [t.tax_code_id and t.base_code_id.id for t in self.pool.get('account.tax').browse(cr,uid,all_taxes)] + [t.ref_tax_code_id and t.ref_base_code_id.id for t in self.pool.get('account.tax').browse(cr,uid,all_taxes)]
			base_codes = list(set(base_codes))

			found_tax = False
			temp = []
			i=0
			for line in res:
				i+=1
				sign = invoice_browse.type =='out_invoice' and -1 or 1
				position = line[2]['credit'] !=0.0 and -1 or 1

				tm = line[2]['debit']!=0.0 and line[2]['debit'] or line[2]['credit']
				if line[2]['tax_amount'] and ( line[2]['tax_code_id'] in codes):
					total_tax += position * sign * tm
					total_tax_amt_currency -= sign * position * line[2]['amount_currency']
					found_tax = True
					
				if line[2]['account_id'] not in rec_payable_id:
					if line[2]['debit']!=False or line[2]['credit']!=False:
						moves.append(line)
						total_trans_amt_currency2 += sign*(line[2]['amount_currency'] or 0.0)	
					if line[2]['tax_amount'] and line[2]['tax_code_id'] in base_codes:
						temp.append(line)
				else:
					moves_ar_ap = line
					total_trans_amt_currency += line[2]['amount_currency']
			found_not_zero = False
			for x in temp:
				if x[2]['debit']!=False or x[2]['credit']!=False:
					found_not_zero = True
				
			# print "moves_ar_ap-----------",moves_ar_ap
			# if moves_ar_ap and invoice_browse.use_kmk_ar_ap:
			# 	t_moves_arp_ap=moves_ar_ap[2].copy()
			# 	amt = t_moves_arp_ap['debit'] not in (0.0,False) and t_moves_arp_ap['debit'] or (-1 * t_moves_arp_ap['credit'])
			# 	cur_obj =self.pool.get('res.currency')
			# 	context_rate = {}
			# 	context_rate.update({'date':invoice_browse.date_invoice or time.strftime('%Y-%m-%d'),'reverse':False,'trans_currency':invoice_browse.currency_id and invoice_browse.currency_id.id or False})
			# 	amount_currency = cur_obj.computerate(cr, uid, invoice_browse.currency_id.id,invoice_browse.company_id.tax_base_currency.id , amt, context=context_rate)

			# 	t_moves_arp_ap.update({'amount_currency':amount_currency,'currency_id':invoice_browse.company_id and invoice_browse.company_id.tax_base_currency.id})
			# 	moves_ar_ap = (0,0,t_moves_arp_ap)
			
			print "moves_ar_ap-----------",total_tax,moves_ar_ap[2]['debit'],moves_ar_ap[2]['credit']
			if moves_ar_ap and total_tax > 0.0 and found_tax and found_not_zero:
				temp = moves_ar_ap[2].copy()
				temp2 = moves_ar_ap[2].copy()
				debit = moves_ar_ap[2]['debit']>0.0 and moves_ar_ap[2]['debit'] - total_tax or moves_ar_ap[2]['debit']
				credit = moves_ar_ap[2]['credit']>0.0 and moves_ar_ap[2]['credit'] - total_tax or moves_ar_ap[2]['credit']
				debit2 = moves_ar_ap[2]['debit']>0.0 and total_tax or 0.0
				credit2 = moves_ar_ap[2]['credit']>0.0 and total_tax or 0.0

				# if invoice_browse.currency_id.id != invoice_browse.company_id.currency_id.id or invoice_browse.currency_tax_id.id !=invoice_browse.company_id.currency_id.id or invoice_browse.use_kmk_ar_ap:
				# 	temp.update({
				# 		'amount_currency':(invoice_browse.currency_id.id != invoice_browse.company_id.currency_id.id or invoice_browse.use_kmk_ar_ap) and (total_trans_amt_currency-total_tax_amt_currency) or False,
				# 		'currency_id':(invoice_browse.currency_id.id != invoice_browse.company_id.currency_id.id and not invoice_browse.use_kmk_ar_ap and invoice_browse.currency_id.id) or (invoice_browse.use_kmk_ar_ap and invoice_browse.currency_tax_id and invoice_browse.currency_tax_id.id) or False,
				# 		})

				# 	temp2.update({
				# 		'amount_currency':total_tax_amt_currency,
				# 		'ar_ap_tax':True,
				# 		'currency_id':invoice_browse.currency_tax_id and invoice_browse.currency_tax_id.id or invoice_browse.currency_id.id,})
				
				is_kmk_tax = invoice_browse.currency_tax_id.id == invoice_browse.company_id.tax_base_currency.id
				if is_kmk_tax:
					if invoice_browse.currency_id.id == invoice_browse.company_id.currency_id.id and invoice_browse.use_kmk_ar_ap:
						temp.update({
							'amount_currency':(total_trans_amt_currency2-total_tax_amt_currency),
							'currency_id':invoice_browse.currency_tax_id.id,
							})
					elif invoice_browse.currency_id.id != invoice_browse.company_id.currency_id.id:
						if invoice_browse.use_kmk_ar_ap:
							temp.update({
								'amount_currency':(total_trans_amt_currency-total_tax_amt_currency),
								'currency_id': invoice_browse.currency_tax_id.id,
								})
						else:
							temp.update({
								'amount_currency':(total_trans_amt_currency-total_tax_amt_currency),
								'currency_id': invoice_browse.currency_id.id!=invoice_browse.company_id.currency_id.id and invoice_browse.currency_id.id or False,
								})

					temp2.update({
						'amount_currency':total_tax_amt_currency,
						'ar_ap_tax':True,
						'currency_id': invoice_browse.currency_tax_id.id,})
				else:
					temp.update({
						'amount_currency':invoice_browse.currency_id.id != invoice_browse.company_id.currency_id.id and (total_trans_amt_currency-total_tax_amt_currency) or 0.0,
						'currency_id':invoice_browse.currency_id.id!=invoice_browse.company_id.currency_id.id and invoice_browse.currency_id.id or False,
						})
					temp2.update({
						'amount_currency':total_tax_amt_currency,
						'ar_ap_tax':True,
						'currency_id':invoice_browse.currency_id.id!=invoice_browse.company_id.currency_id.id and invoice_browse.currency_id.id or False,})



				temp.update({'debit':abs(debit),'credit':abs(credit),})
				temp2.update({'debit':abs(debit2),'credit':abs(credit2)})

				moves.append((0,0,temp))
				moves.append((0,0,temp2))
			elif moves_ar_ap and not found_tax:
				moves.append(moves_ar_ap)
			elif moves_ar_ap and found_tax and not found_not_zero:
				moves.append(moves_ar_ap)
			else:
				moves.append(moves_ar_ap)
			return moves
		else:
			return res

	def action_move_create(self, cr, uid, ids, context=None):
		"""Creates invoice related analytics and financial move lines"""
		ait_obj = self.pool.get('account.invoice.tax')
		cur_obj = self.pool.get('res.currency')
		period_obj = self.pool.get('account.period')
		payment_term_obj = self.pool.get('account.payment.term')
		journal_obj = self.pool.get('account.journal')
		move_obj = self.pool.get('account.move')
		if context is None:
			context = {}
		for inv in self.browse(cr, uid, ids, context=context):
			if not inv.journal_id.sequence_id:
				raise osv.except_osv(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
			if not inv.invoice_line:
				raise osv.except_osv(_('No Invoice Lines!'), _('Please create some invoice lines.'))
			if inv.move_id:
				continue

			ctx = context.copy()
			ctx.update({'lang': inv.partner_id.lang})
			if not inv.date_invoice:
				self.write(cr, uid, [inv.id], {'date_invoice': fields.date.context_today(self,cr,uid,context=context)}, context=ctx)
			company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
			# create the analytical lines
			# one move line per invoice line
			iml = self._get_analytic_lines(cr, uid, inv.id, context=ctx)
			# check if taxes are all computed
			compute_taxes = ait_obj.compute(cr, uid, inv.id, context=ctx)
			self.check_tax_lines(cr, uid, inv, compute_taxes, ait_obj)
			# I disabled the check_total feature
			group_check_total_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'group_supplier_inv_check_total')[1]
			group_check_total = self.pool.get('res.groups').browse(cr, uid, group_check_total_id, context=context)
			if group_check_total and uid in [x.id for x in group_check_total.users]:
				if (inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding/2.0)):
					raise osv.except_osv(_('Bad Total!'), _('Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))

			if inv.payment_term:
				total_fixed = total_percent = 0
				for line in inv.payment_term.line_ids:
					if line.value == 'fixed':
						total_fixed += line.value_amount
					if line.value == 'procent':
						total_percent += line.value_amount
				total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
				if (total_fixed + total_percent) > 100:
					raise osv.except_osv(_('Error!'), _("Cannot create the invoice.\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. In order to avoid rounding issues, the latest line of your payment term must be of type 'balance'."))

			# one move line per tax line
			iml += ait_obj.move_line_get(cr, uid, inv.id)

			entry_type = ''
			if inv.type in ('in_invoice', 'in_refund'):
				ref = inv.reference
				entry_type = 'journal_pur_voucher'
				if inv.type == 'in_refund':
					entry_type = 'cont_voucher'
			else:
				ref = self._convert_ref(cr, uid, inv.number)
				entry_type = 'journal_sale_vou'
				if inv.type == 'out_refund':
					entry_type = 'cont_voucher'
			diff_currency_p = inv.currency_id.id <> company_currency or inv.use_kmk_ar_ap
			# create one move line for the total and possibly adjust the other lines amount
			total = 0
			total_currency = 0

			total, total_currency, iml = self.compute_invoice_totals(cr, uid, inv, company_currency, ref, iml, context=ctx)
			acc_id = inv.account_id.id
			
			name = inv['name'] or inv['supplier_invoice_number'] or '/'
			totlines = False
			if inv.payment_term:
				totlines = payment_term_obj.compute(cr,
						uid, inv.payment_term.id, total, inv.date_invoice or False, context=ctx)
			if totlines:
				res_amount_currency = total_currency
				i = 0
				ctx.update({'date': inv.date_invoice})
				for t in totlines:
					if inv.currency_id.id != company_currency:
						if inv.use_kmk_ar_ap:
							amount_currency = cur_obj.compute(cr, uid, company_currency, inv.currency_id.id, t[1], context=ctx)
						else:   
							amount_currency = cur_obj.compute(cr, uid, company_currency, inv.currency_id.id, t[1], context=ctx)
					else:
						amount_currency = False

					# last line add the diff
					res_amount_currency -= amount_currency or 0
					i += 1
					if i == len(totlines):
						amount_currency += res_amount_currency

					currency_p = (inv.use_kmk_ar_ap and inv.company_id.tax_base_currency.id) \
							or (inv.currency_id.id != inv.company_id.currency_id.id and not inv.use_kmk_ar_ap and inv.company_id.currency_id.id) \
							or False

					iml.append({
						'type': 'dest',
						'name': name,
						'price': t[1],
						'account_id': acc_id,
						'date_maturity': t[0],
						'amount_currency': diff_currency_p \
								and amount_currency or False,
						'currency_id': currency_p,
						'ref': ref,
					})
			else:
				currency_p = (inv.use_kmk_ar_ap and inv.company_id.tax_base_currency.id) \
							or (inv.currency_id.id != inv.company_id.currency_id.id and not inv.use_kmk_ar_ap and inv.company_id.currency_id.id) \
							or False

				iml.append({
					'type': 'dest',
					'name': name,
					'price': total,
					'account_id': acc_id,
					'date_maturity': inv.date_due or False,
					'amount_currency': diff_currency_p \
							and total_currency or False,
					'currency_id': currency_p or False,
					'ref': ref
			})

			date = inv.date_invoice or time.strftime('%Y-%m-%d')

			part = self.pool.get("res.partner")._find_accounting_partner(inv.partner_id)

			line = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, part.id, date, context=ctx)),iml)
			line = self.group_lines(cr, uid, iml, line, inv)

			journal_id = inv.journal_id.id
			journal = journal_obj.browse(cr, uid, journal_id, context=ctx)
			if journal.centralisation:
				raise osv.except_osv(_('User Error!'),
						_('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))

			line = self.finalize_invoice_move_lines(cr, uid, inv, line)
			
			all_taxes = self.pool.get('account.tax').search(cr,uid,[])
			codes = [t.tax_code_id and t.tax_code_id.id  for t in self.pool.get('account.tax').browse(cr,uid,all_taxes)] + [t.ref_tax_code_id and t.ref_tax_code_id.id  for t in self.pool.get('account.tax').browse(cr,uid,all_taxes)]
			codes = list(set(codes))
					
			line_temp = []
			for mvl_temp in line:
				
				if 'tax_code_id' in mvl_temp[2] and mvl_temp[2]['tax_code_id'] in codes:
					dummy_data = mvl_temp[2].copy()
					dummy_data.update({
						'faktur_pajak_source'   :tuple(account.invoice,inv.id),
						'faktur_pajak_no'	   : inv.nomor_faktur_id and inv.nomor_faktur_id.name or ''
						})
					line_temp.append((0,0,dummy_data))
				else:
					line_temp.append(mvl_temp)
			line = line_temp

			move = {
				'ref': inv.reference and inv.reference or inv.name,
				'line_id': line,
				'journal_id': journal_id,
				'date': date,
				'narration': inv.comment,
				'company_id': inv.company_id.id,
			}
			period_id = inv.period_id and inv.period_id.id or False
			ctx.update(company_id=inv.company_id.id,
					   account_period_prefer_normal=True)
			if not period_id:
				period_ids = period_obj.find(cr, uid, inv.date_invoice, context=ctx)
				period_id = period_ids and period_ids[0] or False
			if period_id:
				move['period_id'] = period_id
				for i in line:
					i[2]['period_id'] = period_id

			ctx.update(invoice=inv)
			move_id = move_obj.create(cr, uid, move, context=ctx)
			new_move_name = move_obj.browse(cr, uid, move_id, context=ctx).name
			# make the invoice point to that move
		
			self.write(cr, uid, [inv.id], {'move_id': move_id,'period_id':period_id, 'move_name':new_move_name}, context=ctx)
			# Pass invoice in context in method post: used if you want to get the same
			# account move reference when creating the same invoice after a cancelled one:
			# link to account_move post
			move_obj.post(cr, uid, [move_id], context=ctx)
		self._log_event(cr, uid, ids)
		return True


	# def action_move_create(self, cr, uid, ids, context=None):
	#	 """Creates invoice related analytics and financial move lines"""
	#	 print "================faktur=============="
	#	 ait_obj = self.pool.get('account.invoice.tax')
	#	 cur_obj = self.pool.get('res.currency')
	#	 period_obj = self.pool.get('account.period')
	#	 payment_term_obj = self.pool.get('account.payment.term')
	#	 journal_obj = self.pool.get('account.journal')
	#	 move_obj = self.pool.get('account.move')
	#	 if context is None:
	#		 context = {}
	#	 for inv in self.browse(cr, uid, ids, context=context):
	#		 if not inv.journal_id.sequence_id:
	#			 raise osv.except_osv(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
	#		 if not inv.invoice_line:
	#			 raise osv.except_osv(_('No Invoice Lines!'), _('Please create some invoice lines.'))
	#		 if inv.move_id:
	#			 continue

	#		 ctx = context.copy()
	#		 ctx.update({'lang': inv.partner_id.lang})
	#		 if not inv.date_invoice:
	#			 self.write(cr, uid, [inv.id], {'date_invoice': fields.date.context_today(self,cr,uid,context=context)}, context=ctx)
	#		 company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
	#		 # create the analytical lines
	#		 # one move line per invoice line
	#		 iml = self._get_analytic_lines(cr, uid, inv.id, context=ctx)
	#		 # check if taxes are all computed
	#		 compute_taxes = ait_obj.compute(cr, uid, inv.id, context=ctx)
	#		 self.check_tax_lines(cr, uid, inv, compute_taxes, ait_obj)
	#		 # I disabled the check_total feature
	#		 group_check_total_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'group_supplier_inv_check_total')[1]
	#		 group_check_total = self.pool.get('res.groups').browse(cr, uid, group_check_total_id, context=context)
	#		 if group_check_total and uid in [x.id for x in group_check_total.users]:
	#			 if (inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding/2.0)):
	#				 raise osv.except_osv(_('Bad Total!'), _('Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))

	#		 if inv.payment_term:
	#			 total_fixed = total_percent = 0
	#			 for line in inv.payment_term.line_ids:
	#				 if line.value == 'fixed':
	#					 total_fixed += line.value_amount
	#				 if line.value == 'procent':
	#					 total_percent += line.value_amount
	#			 total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
	#			 if (total_fixed + total_percent) > 100:
	#				 raise osv.except_osv(_('Error!'), _("Cannot create the invoice.\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. In order to avoid rounding issues, the latest line of your payment term must be of type 'balance'."))

	#		 # one move line per tax line
	#		 iml += ait_obj.move_line_get(cr, uid, inv.id)

	#		 entry_type = ''
	#		 if inv.type in ('in_invoice', 'in_refund'):
	#			 ref = inv.reference
	#			 entry_type = 'journal_pur_voucher'
	#			 if inv.type == 'in_refund':
	#				 entry_type = 'cont_voucher'
	#		 else:
	#			 ref = self._convert_ref(cr, uid, inv.number)
	#			 entry_type = 'journal_sale_vou'
	#			 if inv.type == 'out_refund':
	#				 entry_type = 'cont_voucher'
	#		 diff_currency_p = inv.currency_id.id <> company_currency
	#		 # create one move line for the total and possibly adjust the other lines amount
	#		 total = 0
	#		 total_currency = 0
	#		 total, total_currency, iml = self.compute_invoice_totals(cr, uid, inv, company_currency, ref, iml, context=ctx)
	#		 print "----------------faktur pajak---------------",iml
	#		 acc_id = inv.account_id.id
			
	#		 name = inv['name'] or inv['supplier_invoice_number'] or '/'
	#		 totlines = False
	#		 if inv.payment_term:
	#			 totlines = payment_term_obj.compute(cr,
	#					 uid, inv.payment_term.id, total, inv.date_invoice or False, context=ctx)
	#		 if totlines:
	#			 res_amount_currency = total_currency
	#			 i = 0
	#			 ctx.update({'date': inv.date_invoice})
	#			 for t in totlines:
	#				 if inv.currency_id.id != company_currency:
	#					 amount_currency = cur_obj.compute(cr, uid, company_currency, inv.currency_id.id, t[1], context=ctx)
	#				 else:
	#					 amount_currency = False

	#				 # last line add the diff
	#				 res_amount_currency -= amount_currency or 0
	#				 i += 1
	#				 if i == len(totlines):
	#					 amount_currency += res_amount_currency

	#				 iml.append({
	#					 'type': 'dest',
	#					 'name': name,
	#					 'price': t[1],
	#					 'account_id': acc_id,
	#					 'date_maturity': t[0],
	#					 'amount_currency': diff_currency_p \
	#							 and amount_currency or False,
	#					 'currency_id': diff_currency_p \
	#							 and inv.currency_id.id or False,
	#					 'ref': ref,
	#				 })
	#		 else:
	#			 iml.append({
	#				 'type': 'dest',
	#				 'name': name,
	#				 'price': total,
	#				 'account_id': acc_id,
	#				 'date_maturity': inv.date_due or False,
	#				 'amount_currency': diff_currency_p \
	#						 and total_currency or False,
	#				 'currency_id': diff_currency_p \
	#						 and inv.currency_id.id or False,
	#				 'ref': ref
	#		 })

	#		 date = inv.date_invoice or time.strftime('%Y-%m-%d')

	#		 part = self.pool.get("res.partner")._find_accounting_partner(inv.partner_id)

	#		 line = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, part.id, date, context=ctx)),iml)

	#		 line = self.group_lines(cr, uid, iml, line, inv)

	#		 journal_id = inv.journal_id.id
	#		 journal = journal_obj.browse(cr, uid, journal_id, context=ctx)
	#		 if journal.centralisation:
	#			 raise osv.except_osv(_('User Error!'),
	#					 _('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))

	#		 line = self.finalize_invoice_move_lines(cr, uid, inv, line)			
	#		 move = {
	#			 'ref': inv.reference and inv.reference or inv.name,
	#			 'line_id': line,
	#			 'journal_id': journal_id,
	#			 'date': date,
	#			 'narration': inv.comment,
	#			 'company_id': inv.company_id.id,
	#		 }
	#		 period_id = inv.period_id and inv.period_id.id or False
	#		 ctx.update(company_id=inv.company_id.id,
	#					account_period_prefer_normal=True)
	#		 if not period_id:
	#			 period_ids = period_obj.find(cr, uid, inv.date_invoice, context=ctx)
	#			 period_id = period_ids and period_ids[0] or False
	#		 if period_id:
	#			 move['period_id'] = period_id
	#			 for i in line:
	#				 i[2]['period_id'] = period_id

	#		 ctx.update(invoice=inv)
	#		 move_id = move_obj.create(cr, uid, move, context=ctx)
	#		 new_move_name = move_obj.browse(cr, uid, move_id, context=ctx).name
	#		 # make the invoice point to that move
		
	#		 self.write(cr, uid, [inv.id], {'move_id': move_id,'period_id':period_id, 'move_name':new_move_name}, context=ctx)
	#		 # Pass invoice in context in method post: used if you want to get the same
	#		 # account move reference when creating the same invoice after a cancelled one:
	#		 # link to account_move post
	#		 move_obj.post(cr, uid, [move_id], context=ctx)
	#	 self._log_event(cr, uid, ids)
	#	 return True
	
	def onchange_journal_id(self, cr, uid, ids, journal_id=False, partner_id=False, context=None):
		result = {}
		if journal_id and partner_id:
			journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
			partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
			currency_id = journal.currency and journal.currency.id or journal.company_id.currency_id.id
			acc_id = 0

			cur = self.pool.get('res.currency').browse(cr, uid, currency_id, context=context)
			if cur.name == "USD":
				acc_id = partner.property_account_receivable_usd and partner.property_account_receivable_usd.id
			elif cur.name == "IDR":
				acc_id = partner.property_account_receivable and partner.property_account_receivable.id
			company_id = journal.company_id.id
			result = {'value': {
					'account_id': acc_id,
					'currency_id': currency_id,
					'company_id': company_id,
					}
				}
		return result

	def button_reset_taxes(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		ctx = context.copy()
		ait_obj = self.pool.get('account.invoice.tax')
		for id in ids:
			inv = self.pool.get('account.invoice').browse(cr, uid, id)
			cr.execute("DELETE FROM account_invoice_tax WHERE invoice_id=%s AND manual is False", (id,))
			partner = self.browse(cr, uid, id, context=ctx).partner_id
			if partner.lang:
				ctx.update({'lang': partner.lang})
			for taxe in ait_obj.compute(cr, uid, id, context=ctx).values():
				## ####### custom edit : so the tax will always rounded by 1
				if inv and inv.currency_tax_id and inv.currency_tax_id.id==inv.company_id.tax_base_currency.id and inv.currency_id.id==inv.company_id.tax_base_currency.id:
					taxe['base'] = round(taxe['base'])
					taxe['amount'] = round(taxe['amount'])
					taxe['base_amount'] = round(taxe['base_amount'])
					taxe['tax_amount'] = round(taxe['tax_amount'])
				
				ait_obj.create(cr, uid, taxe)
		# Update the stored value (fields.function), so we write to trigger recompute
		self.pool.get('account.invoice').write(cr, uid, ids, {'invoice_line':[]}, context=ctx)
		return True
account_invoice()


class account_invoice_faktur_pajak(osv.osv):
	_name = "account.invoice.faktur.pajak"
	_columns = {
		'name' : fields.char('No. Faktur Pajak', size=120),
		'partner_id': fields.many2one('res.partner', string="Partner"),
		'tax_amount': fields.float('Tax Amount', digits_compute= dp.get_precision('Account')),
		'tax_base_amount' : fields.float('Base Amount', digits_compute= dp.get_precision('Account')),
		'tax_id': fields.many2one('account.tax', 'Tax'),
		'tax_date' : fields.date('Tax Date'),
		'invoice_id' : fields.many2one('account.invoice','Invoice')
	}

account_invoice_faktur_pajak()

