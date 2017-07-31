from osv import fields, osv
from report import report_sxw
import pooler
import time
from report.render import render
from tools.translate import _
from datetime import datetime

class production_memo_parser(report_sxw.rml_parse):    
	def __init__(self, cr, uid, name, context=None):
		super(production_memo_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time':time,
			'xdate':self._xdate,
			'get_unit_group':self._get_unit_group,
			'get_uom_base':self._get_uom_base,
			'uom_to_base':self._uom_to_base,
			'get_print_user_time':self. _get_print_user_time,
			'get_order_line':self._get_order_line,
        })
           
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

	def _get_unit_group(self,prod_memo_obj):
		res=[]
		prod_memo_group={}
		key=prod_memo_obj.manufacturer.name or ''
		prod_memo_group[key]=['']
		prod_memo_group[key][0]=key

		for line in prod_memo_obj.goods_lines:
			key=line.manufacturer.name or ''
			if (key != ''):
				if (key not in prod_memo_group):
					prod_memo_group[key]=['']
					prod_memo_group[key][0]=key

		for x in prod_memo_group.keys():
			res.append(prod_memo_group[x])
		return res

	def _get_uom_base(self,sale_type):
		if sale_type == 'export':
			uom_base = 'KGS'
		elif sale_type == 'local':
			uom_base = 'BALES'
		else:
			uom_base = 'KGS'
		return uom_base

	def _uom_to_base(self,sale_type,qty,uom_source):
		cr = self.cr
		uid = self.uid
		if sale_type == 'export':
			uom_base = 'KGS'
		elif sale_type == 'local':
			uom_base = 'BALES'
		else:
			uom_base = 'KGS'
		base = self.pool.get('product.uom').search(cr,uid,[('name','=',uom_base)])
		qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, qty, to_uom_id=base and base[0] or False)
		return qty_result

	def _get_order_line(self,order_id,sequence_line,product_id,context=None):
		sale_line_obj   = self.pool.get('sale.order.line')
		sale_line_ids   = sale_line_obj.search(self.cr, self.uid,[('order_id','=',order_id),
																('sequence_line','=',sequence_line),
																('product_id','=',product_id)])
		order_lines = sale_line_obj.browse(self.cr, self.uid,sale_line_ids)
		if len(order_lines) > 0:
			res = sale_line_obj.browse(self.cr, self.uid,sale_line_ids)[0]
		else:
			res = False
		return res

report_sxw.report_sxw('report.production.memo.form', 'production.memo', 'ad_production_memo/report/production_memo_form.mako', parser=production_memo_parser,header=False) 