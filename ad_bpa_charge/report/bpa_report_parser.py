import re
import time
import xlwt
from openerp.report import report_sxw
from ad_account_optimization.report.report_engine_xls import report_xls
import cStringIO
from xlwt import Workbook, Formula
from tools.translate import _

class bpa_report_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(bpa_report_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'get_result':self._get_result,
			'report_title':self._get_title,
			'report_number':self._get_number,
			'report_date':self._get_date,
		})

	def _get_title(self, data, objects):
		res = ""
		data=data['form']
		if data['type_of_charge'][1].encode('utf-8').upper()=='FREIGHT':
			res = "FREIGHT"
		elif data['type_of_charge'][1].encode('utf-8').upper()=='TRANSPORT':
			res = "TRANSPORT"
		elif data['type_of_charge'][1].encode('utf-8').upper()=='EMKL':
			res = "EMKL"
		elif data['type_of_charge'][1].encode('utf-8').upper()=='LIFT ON LIFT OFF':
			res = "LIFT ON LIFT OFF"
		elif data['type_of_charge'][1].encode('utf-8').upper()=='[FGHE] FINISH GOOD HANDLING EXPORT':
			res = "KBKB EXPORT"
		elif data['type_of_charge'][1].encode('utf-8').upper()=='[FGHL] FINISH GOOD HANDLING LOCAL':
			res = "KBKB LOCAL"
		elif data['type_of_charge'][1].encode('utf-8').upper()=='SALES COMMISSION':
			res = "SALES COMMISSION"

		return res

	def _get_number(self, data, objects):
		return data['form']['reference'].encode('utf-8')

	def _get_date(self, data, objects):
		return time.strftime('%Y-%m-%d')

	def _get_result(self, data):
		res = []
		data=data['form']

		if data['type_of_charge'][1].encode('utf-8').upper() in ('FREIGHT','TRANSPORT','EMKL','LIFT ON LIFT OFF'):
			query = "\
				(SELECT \
					e.partner_code as partner_code, substring(e.name from 1 for 16) as partner_name, substring(coalesce(o.name,o1.name) from 1 for 16) as party, c.name as picking_name, \
					to_char(c.date_done,'DD/MM/YY') as picking_date, b.internal_number as related_invoice, \
					b.bl_number, to_char(b.bl_date,'DD/MM/YY') as bl_date, to_char(d.date_invoice,'DD/MM/YY') as bill_date, \
					to_char(d.date_due,'DD/MM/YY') as due_date, f.name as curr, sum(a.price_unit*a.quantity) as amount, a.price_unit, sum(a.quantity) as qty,\
					(case lower(g.name) \
						when 'freight' then k.name \
						else '' end) as dest_port,\
					(case lower(g.name) \
						when 'freight' then \
							coalesce(r.name,'False')\
						when 'emkl' then c.container_number||' '||\
							coalesce(r.name,'False')\
						when 'transport' then c.truck_number\
						else '' end) as container,\
					d.supplier_invoice_number as inv_number, substring(p.name from 1 for 16) as shipping_lines\
				FROM\
					account_invoice_line a\
					LEFT JOIN account_invoice b ON b.id=a.invoice_related_id\
					LEFT JOIN stock_picking c ON c.id=a.picking_related_id \
					\
					INNER JOIN account_invoice d ON d.id=a.invoice_id \
					INNER JOIN res_partner e ON e.id=d.partner_id\
					INNER JOIN res_currency f ON f.id=d.currency_id\
					\
					LEFT JOIN charge_type g ON g.id=a.type_of_charge\
					LEFT JOIN stock_transporter_charge h ON h.id=c.forwading_charge\
					LEFT JOIN stock_transporter_charge i ON i.id=c.trucking_charge\
					LEFT JOIN stock_porters_charge j ON j.id=c.porters_charge\
					LEFT JOIN res_port k ON k.id=h.port_id\
					LEFT JOIN product_uom l ON l.id=h.uom_id\
					LEFT JOIN product_uom m ON m.id=i.uom_id\
					LEFT JOIN product_uom n ON l.id=j.uom_id\
					LEFT JOIN res_partner o ON o.id=b.partner_id\
					LEFT JOIN res_partner o1 ON o1.id=c.partner_id\
					LEFT JOIN stock_transporter p ON p.id=c.shipping_lines\
					LEFT JOIN container_size q ON q.id=c.container_size\
					LEFT JOIN container_type r ON r.id=q.type\
				WHERE\
					d.type='in_invoice' and a.type_of_charge='%s' and d.reference='%s'\
				GROUP BY\
					e.partner_code, e.name, coalesce(o.name,o1.name), c.name, to_char(c.date_done,'DD/MM/YY'), b.internal_number, \
					b.bl_number, to_char(b.bl_date,'DD/MM/YY'), to_char(d.date_invoice,'DD/MM/YY'), \
					to_char(d.date_due,'DD/MM/YY'), f.name, dest_port, a.price_unit, container, d.supplier_invoice_number, p.name\
				ORDER BY\
					b.internal_number, e.partner_code, c.name  asc)\
				UNION ALL\
				(SELECT \
					e.partner_code as partner_code, e.name as partner_name, coalesce(k.name,k1.name) as party, c.name as picking_name, \
					to_char(c.date_done,'DD/MM/YY') as picking_date, b.internal_number as related_invoice, \
					b.bl_number, to_char(b.bl_date,'DD/MM/YY') as bl_date, to_char(d.request_date,'DD/MM/YY') as bill_date, \
					to_char(d.due_date,'DD/MM/YY') as due_date, f.name as curr, sum(a.debit) as amount, 0 as price_unit, sum(0) as qty,\
					'' as dest_port, \
					(case lower(g.name) \
						when 'freight' then coalesce(p.name,'False')\
						when 'emkl' then c.container_number||' '||coalesce(p.name,'False')\
						when 'transport' then coalesce(c.truck_number,'False') \
						when 'lift on lift off' then coalesce(c.container_number,'False')||' '||coalesce(p.name,'False')\
						else '' end) as container,\
					a.name as inv_number, m.name as shipping_lines\
				FROM\
					ext_transaksi_line a\
					LEFT JOIN account_invoice b ON b.id=a.invoice_related_id\
					LEFT JOIN stock_picking c ON c.id=a.picking_related_id \
					INNER JOIN ext_transaksi d ON d.id=a.ext_transaksi_id \
					INNER JOIN res_partner e ON e.id=a.partner_id\
					INNER JOIN res_currency f ON f.id=d.currency_id\
					LEFT JOIN charge_type g ON g.id=a.type_of_charge\
					LEFT JOIN stock_transporter_charge h ON h.id=c.forwading_charge\
					LEFT JOIN stock_transporter_charge i ON i.id=c.trucking_charge\
					LEFT JOIN stock_porters_charge j ON j.id=c.porters_charge\
					LEFT JOIN res_partner k ON k.id=b.partner_id\
					LEFT JOIN res_partner k1 ON k1.id=c.partner_id\
					LEFT JOIN product_uom l ON l.id=h.uom_id\
					LEFT JOIN stock_transporter m ON m.id=c.shipping_lines\
					LEFT JOIN container_type n ON n.id=h.size_container\
					LEFT JOIN container_size o ON o.id=c.container_size\
					LEFT JOIN container_type p on p.id=o.type\
				WHERE\
					a.type_of_charge='%s' and (d.number='%s' or d.name='%s') and d.is_bpa='t'\
				GROUP BY\
					e.partner_code, e.name, coalesce(k.name,k1.name), c.name, to_char(c.date_done,'DD/MM/YY'), b.internal_number, \
					b.bl_number, to_char(b.bl_date,'DD/MM/YY'), to_char(d.request_date,'DD/MM/YY'), \
					to_char(d.due_date,'DD/MM/YY'), f.name, dest_port, price_unit, container, a.name, m.name\
				ORDER BY\
					b.internal_number, e.partner_code, c.name asc)\
				"%(data['type_of_charge'][0],data['reference'],data['type_of_charge'][0],data['reference'],data['reference'])
			self.cr.execute(query)
			results = self.cr.dictfetchall()
			res_grouped = {}
			for res in results:
				key = res['curr']
				if key not in res_grouped:
					res_grouped.update({key:[]})
				res_grouped[key].append(res)

			#group by party
			for key in res_grouped:
				res_grouped2={}
				for res in res_grouped[key]:
					key2 = (res['partner_code'],res['partner_name'])
					if key2 not in res_grouped2:
						res_grouped2.update({key2:[]})
					res_grouped2[key2].append(res)
				res_grouped[key]=res_grouped2

			#group by party and due_date
			res_grouped_1 = res_grouped.copy()
			for key in res_grouped_1:
				for key2 in res_grouped_1[key]:
					res_grouped3={}
					for res in res_grouped_1[key][key2]:
						key3 = res['due_date']
						if key3 not in res_grouped3:
							res_grouped3.update({key3:[]})
						res_grouped3[key3].append(res)
					res_grouped_1[key][key2]=res_grouped3
			
			#group by due_date
			res_grouped_2 = {}
			for res in results:
				key = res['due_date']
				if key not in res_grouped_2:
					res_grouped_2.update({key:[]})
				res_grouped_2[key].append(res)

			return results,res_grouped,res_grouped_1,res_grouped_2
		elif data['type_of_charge'][1].encode('utf-8').upper() in ('[FGHE] FINISH GOOD HANDLING EXPORT','[FGHL] FINISH GOOD HANDLING LOCAL'):
			query = "\
				SELECT \
					e.partner_code as partner_code, e.name as partner_name, k.name as party, \
					coalesce(c.name,'') as picking_name, to_char(c.date_done,'DD/MM/YY') as picking_date,\
					coalesce(b.number,coalesce(b.internal_number,'')) as related_invoice, \
					to_char(d.request_date,'DD/MM/YY') as bill_date, \
					to_char(d.due_date,'DD/MM/YY') as due_date, f.name as curr, sum(a.debit) as amount,\
					j.cost as cost\
				FROM\
					ext_transaksi_line a\
					LEFT JOIN account_invoice b ON b.id=a.invoice_related_id\
					LEFT JOIN stock_picking c ON c.id=a.picking_related_id \
					INNER JOIN ext_transaksi d ON d.id=a.ext_transaksi_id \
					INNER JOIN res_partner e ON e.id=a.partner_id\
					INNER JOIN res_currency f ON f.id=d.currency_id\
					LEFT JOIN charge_type g ON g.id=a.type_of_charge\
					LEFT JOIN stock_transporter_charge h ON h.id=c.forwading_charge\
					LEFT JOIN stock_transporter_charge i ON i.id=c.trucking_charge\
					LEFT JOIN stock_porters_charge j ON j.id=c.porters_charge\
					LEFT JOIN res_partner k ON k.id=b.partner_id\
				WHERE\
					a.type_of_charge='%s' and (d.number='%s' or d.name='%s') and d.is_bpa='t'\
				GROUP BY\
					e.partner_code, e.name, k.name, \
					c.name, to_char(c.date_done,'DD/MM/YY'), \
					coalesce(b.number,coalesce(b.internal_number,'')), \
					to_char(d.request_date,'DD/MM/YY'), \
					to_char(d.due_date,'DD/MM/YY'), f.name, j.cost\
				ORDER BY\
					e.partner_code, coalesce(b.number,coalesce(b.internal_number,'')), c.name asc\
				"%(data['type_of_charge'][0],data['reference'],data['reference'])
			self.cr.execute(query)
			results = self.cr.dictfetchall()
			res_grouped = {}
			for res in results:
				key = res['curr']
				if key not in res_grouped:
					res_grouped.update({key:[]})
				res_grouped[key].append(res)

			for key in res_grouped:
				res_grouped2={}
				for res in res_grouped[key]:
					key2 = (res['partner_code'],res['partner_name'])
					if key2 not in res_grouped2:
						res_grouped2.update({key2:[]})
					res_grouped2[key2].append(res)
				res_grouped[key]=res_grouped2

			return res_grouped
		elif data['type_of_charge'][1].encode('utf-8').upper() in ('SALES COMMISSION'):
			# query = "\
			# 	SELECT\
			# 	c.number as inv_no, to_char(c.date_invoice,'DD/MM/YY') as inv_date, c.date_invoice as inv_date2,\
			# 	e.name as lc_batch, e.sequence_line as contract, f.name as party, \
			# 	h.name as prod_name, SUM(b.price_subtotal) as amt1, c.amount_total as amt2, \
			# 	i.name as agent_name, coalesce(d.commission_percentage,0) as comm_percent, \
			# 	coalesce(d.commission_amount_without_fob,0) as comm_amt1, c.amount_freight as freight, c.amount_insurance as insurance,\
			# 	j.code as incoterms, j.fob_compute as fob_compute, a.desciption as bill_number, a.bill_date as bill_date\
			# 	FROM \
			# 	account_bill_passing_line a\
			# 	LEFT JOIN account_invoice_line b ON b.invoice_id = a.invoice_related_id\
			# 	INNER JOIN account_invoice c ON c.id=a.invoice_related_id\
			# 	INNER JOIN account_invoice_commission d ON d.invoice_id=a.invoice_related_id \
			# 	LEFT JOIN (SELECT e1.invoice_line_id as inv_line_id, e3.name, e4.sequence_line \
			# 				FROM stock_move e1 \
			# 				LEFT JOIN letterofcredit_product_line e2 ON e2.id=e1.lc_product_line_id \
			# 				LEFT JOIN letterofcredit e3 ON e3.id=e2.lc_id \
			# 				LEFT JOIN sale_order_line e4 ON e4.id=e1.sale_line_id \
			# 				) e ON e.inv_line_id=b.id \
			# 	LEFT JOIN res_partner f ON f.id=c.partner_id \
			# 	LEFT JOIN product_product g ON g.id=b.product_id \
			# 	LEFT JOIN product_template h ON h.id=g.product_tmpl_id \
			# 	INNER JOIN res_partner i ON i.id=a.partner_id \
			# 	LEFT JOIN stock_incoterms j ON j.id=c.incoterms \
			# 	WHERE\
			# 	a.bill_id=(SELECT id FROM account_bill_passing WHERE name='%s')\
			# 	GROUP BY\
			# 	c.number, to_char(c.date_invoice,'DD/MM/YY'), c.date_invoice,\
			# 	e.name, e.sequence_line, f.name, \
			# 	h.name, c.amount_total, \
			# 	i.name, d.commission_percentage, \
			# 	d.commission_amount_without_fob, c.amount_freight, c.amount_insurance,\
			# 	j.code, j.fob_compute, a.desciption,a.bill_date \
			# 	ORDER BY\
			# 	c.date_invoice,c.number,e.sequence_line asc\
			# 	"%(data['reference'])
			query = "\
				SELECT \
					abpl.desciption as bill_number, to_char(abpl.bill_date,'DD/MM/YYYY') as bill_date, to_char(abp.date_due,'DD/MM/YYYY') as due_date,* \
				FROM \
					commission_detail('2015-01-01'::date,(SELECT date_entry FROM account_bill_passing WHERE name='%s' limit 1)::date, \
						(select b.sale_type \
						from account_bill_passing_line a \
						inner join account_invoice b on b.id=a.invoice_related_id \
						where a.bill_id=(SELECT id FROM account_bill_passing WHERE name='%s') limit 1)::text) as cd \
					INNER JOIN account_bill_passing_line abpl ON abpl.invoice_related_id=cd.inv_id and abpl.partner_id=cd.agent_db_id \
					INNER JOIN account_bill_passing abp ON abp.id=abpl.bill_id\
				WHERE abpl.bill_id=(SELECT id FROM account_bill_passing WHERE name='%s') \
				"%(data['reference'],data['reference'],data['reference'])
			print ":::::::::::::::::", query
			self.cr.execute(query)
			results = self.cr.dictfetchall()
			return results
	
	def _get_company_currency(self):
		return self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id

	def _get_amount_company_currency(self, from_curr, amount, date):
		currency_usd = self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id.currency_id
		return self.pool.get('res.currency').compute(cr, uid, from_curr, currency_usd.id, amount, context={'date':date})

# advance_report_xls('report.advance.report','advance.report.wizard','addons/ad_account_reports/payment_overdue.mako', parser=advance_report_parser, header=False)
report_sxw.report_sxw('report.bpa.report.freight.mako','wizard.bpa.report','addons/ad_bpa_charge/report/bpa_report_freight.mako', parser=bpa_report_parser, header=False)
report_sxw.report_sxw('report.bpa.report.emkl.mako','wizard.bpa.report','addons/ad_bpa_charge/report/bpa_report_emkl.mako', parser=bpa_report_parser, header=False)
report_sxw.report_sxw('report.bpa.report.comm.mako','wizard.bpa.report','addons/ad_bpa_charge/report/bpa_report_comm.mako', parser=bpa_report_parser, header=False)
report_sxw.report_sxw('report.bpa.report.kbkb.mako','wizard.bpa.report','addons/ad_bpa_charge/report/bpa_report_kbkb.mako', parser=bpa_report_parser, header=False)
report_sxw.report_sxw('report.bpa.report.mako','wizard.bpa.report','addons/ad_bpa_charge/report/bpa_report.mako', parser=bpa_report_parser, header=False)


class bpa_summary_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(bpa_summary_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
		})

report_sxw.report_sxw('report.bpa.summary.mako','bpa.summary','addons/ad_bpa_charge/report/bpa_summary.mako', parser=bpa_summary_parser, header=False)

class bpa_kbkb_ext_transaksi_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context=None):
		super(bpa_kbkb_ext_transaksi_parser, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'report_title' : self._get_title,
			'report_number':self._get_number,
			'report_date':self._get_date,
		})

	def _get_title(self, data, objects):
		type_charge = False
		res = ""
		obj = objects and objects[0] or False
		if not obj:
			return res
		for line in obj.ext_line:
			if line.type_of_charge:
				type_charge = line.type_of_charge
			else:
				continue
		if type_charge and type_charge.name.upper()=='RAW MATERIAL HANDLING':
			res = "KBKB RM"
		elif type_charge and type_charge.name.upper()=='FREIGHT':
			res = "FREIGHT"
		elif type_charge and type_charge.name.upper()=='TRANSPORT':
			res = "TRANSPORT"
		elif type_charge and type_charge.name.upper()=='EMKL':
			res = "EMKL"
		elif type_charge and type_charge.name.upper()=='LIFT ON LIFT OFF':
			res = "LIFT ON LIFT OFF"
		elif type_charge and type_charge.name.upper()=='FINISH GOOD HANDLING EXPORT':
			res = "KBKB EXPORT"
		elif type_charge and type_charge.name.upper()=='FINISH GOOD HANDLING LOCAL':
			res = "KBKB LOCAL"
		elif type_charge and type_charge.name.upper()=='SALES COMMISSION':
			res = "SALES COMMISSION"

		return res

	def _get_number(self, data, objects):
		return objects and objects[0].number or ""

	def _get_date(self, data, objects):
		return objects and objects[0].request_date!='False' and objects[0].request_date or time.strftime('%Y-%m-%d')



report_sxw.report_sxw('report.bpa.report.kbkb.ext.mako','ext.transaksi','addons/ad_bpa_charge/report/bpa_report_kbkb_ext.mako', parser=bpa_kbkb_ext_transaksi_parser, header=False)