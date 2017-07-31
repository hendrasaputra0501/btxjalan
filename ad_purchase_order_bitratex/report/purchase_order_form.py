import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from datetime import datetime
from ad_num2word_id import num2word

class purchase_order_parser(report_sxw.rml_parse):    
	def __init__(self, cr, uid, name, context=None):
		super(purchase_order_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
		'time':time,
		'xdate':self._xdate,
		'xdatepmonth':self._xdatepmonth,
		'xdatepday':self._xdatepday,
		'call_num2word':self._call_num2word,
		'get_print_user_time':self._get_print_user_time,
		'get_mr_date':self.get_mr_date,
		'check_alldiscounts_ispercentage': self.check_alldiscounts_ispercentage,
		'get_amount_line': self._get_amount_line,
		}),
	def _call_num2word(self,amount_total,cur):
		amt_id=num2word.num2word_id(amount_total,cur).decode('utf-8')
		return amt_id

	def get_mr_date(self,mr_lines):
		if mr_lines:
			dates=[]
			for line in mr_lines:
				dates.append(datetime.strptime(line.requisition_id.date_start,'%Y-%m-%d %H:%M:%S'))
			return min(dates).strftime('%Y-%m-%d')
		return False

	def _get_print_user_time(self,context=None):
		cr = self.cr
		uid = self.uid
		curr_user = self.pool.get('res.users').browse(cr, uid, [uid], context=context)[0]
		tlocal = time.localtime()
		slocal = str(tlocal.tm_year) + '-' + str(tlocal.tm_mon) + '-' + str(tlocal.tm_mday) + ' ' + str(tlocal.tm_hour) + ':' + str(tlocal.tm_min) 
		print_user_time = 'Printed By ' + curr_user.partner_id.name + ' On ' + datetime.strptime(slocal,'%Y-%m-%d %H:%M').strftime('%d/%m/%Y %H:%M')
		return print_user_time

	def _xdate(self,x):
		try:
			x1 = x[:10]
		except:
			x1 = ''

		try:
			y = datetime.strptime(x1,'%Y-%m-%d').strftime('%d/%m/%Y')
		except:
			y = x1
		return y

	def _xdatepday(self,x):
		try:
			x1 = x[:10]
		except:
			x1 = ''

		try:

			y = datetime.strptime(x1,'%Y-%m-%d').strftime('%A, %d/%m/%Y')
		except:
			y = x
		return y

	def _xdatepmonth(self,x):
		try:
			x1 = x[:10]
		except:
			x1 = ''

		try:
			y = datetime.strptime(x1,'%Y-%m-%d').strftime('%B %d, %Y')
		except:
			y = x
		return y

	def check_alldiscounts_ispercentage(self, obj):
		is_percentage = False
		n = 0
		for line in obj.order_line:
			for disc in line.discount_ids:
				if n == 0:
					is_percentage = True
					n = 1
				is_percentage = is_percentage and disc.type == 'percentage'
		return is_percentage

	def _get_amount_line(self,line):
		res = {}
		cr=self.cr
		uid=self.uid
		
		cur_obj=self.pool.get('res.currency')
		tax_obj = self.pool.get('account.tax')
		
		order_id = line.order_id
		cur = order_id.pricelist_id.currency_id
		
		taxes_bef = tax_obj.compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, line.order_id.partner_id)
		sub_total_bef_disc = cur_obj.round(cr, uid, cur, taxes_bef['total'])

		disc = self.pool.get('price.discount').compute_discounts(cr, uid, [x.id for x in line.discount_ids], line.price_unit, line.product_qty)
		price_after = disc.get('price_after',line.price_unit)
		taxes_aft = tax_obj.compute_all(cr, uid, line.taxes_id, price_after, line.product_qty, line.product_id, line.order_id.partner_id)
		sub_total_after_disc = cur_obj.round(cr, uid, cur, taxes_aft['total'])
		return {'price_after':price_after, 
				'subtotal_after_discount':sub_total_after_disc,
				'subtotal_before_discount' :sub_total_bef_disc,
				}

report_sxw.report_sxw('report.purchase.order.form','purchase.order','ad_purchase_order_bitratex/report/purchase_order_form.mako',parser=purchase_order_parser,header=False)
