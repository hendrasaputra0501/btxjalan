from openerp.osv import fields,osv

class efaktur_wizard(osv.osv):
	_name = "efaktur.wizard"
	_columns = {
		"filter_by"	: fields.selection([('period','Period'),('date_range','Date Range')],"Filter By",required=True),
		"period_id"	: fields.many2one("account.period","Period"),
		"date_start": fields.date("Start Date"),
		"date_end"	: fields.date("End Date"),
		"type"		: fields.selection([('in',"Masukan"),('out',"Keluaran")],"Jenis Pajak",required=True),
		"tax_code"	: fields.many2many("account.tax","account_tax_efaktur_rel","efaktur_id","tax_code_id","Tax Code",required=False),
		"invoice_ids": fields.many2many("account.invoice","account_invoice_efaktur_rel","efaktur_id","invoice_id","Tax Code",required=False),
		"sale_type"	: fields.selection([('local','Local'),('export','Export')],"Sale Type"),
		"force_period": fields.many2one("account.period","Force Period"),
		"use_force_period": fields.boolean("Use force Period as Masa Faktur"),
		"efaktur_heads_exception": fields.many2many("efaktur.head","efaktur_head_except_wizard_rel","wiz_id","ehead_id","EFaktur Scanned Exceptions"),
		"efaktur_heads_forced": fields.many2many("efaktur.head","efaktur_head_force_wizard_rel","wiz_id","ehead_id","EFaktur Scanned Forced"),
		"goods_type": fields.selection(
			[
			('finish',"Finish Goods"),
			('finish_others',"Finish Goods Others"),
			('raw',"Raw Material"),
			('service',"Service"),
			('stores',"Stores"),
			("waste","Waste"),
			("scrap","Scrap"),
			("asset","Asset")
			],"Goods Type"),
		"type_data"	: fields.selection(
			[
			('import',"Tax Data Ready to be Imported into E-Faktur"),
			('spt_masa_1111',"SPT Masa PPN Form 1111")
			],
			"Filetype",required=True),
	}

	_defaults = {
		"filter_by"	: lambda *a: 'period',
		"period_id"	: lambda self,cr,uid,context:self.pool.get("account.period").find(cr,uid,context=context)[0],
		"force_period" : lambda self,cr,uid,context:self.pool.get("account.period").find(cr,uid,context=context)[0],
		"type"		: lambda *a: 'out',
		"type_data"	: lambda *a: 'import',
		'sale_type'	: lambda *a: 'local',
		'goods_type': lambda *a: 'finish',
	}

	def onchange_period_id(self,cr,uid,ids,period_id):
		val = {}
		if period_id:
			period = self.pool.get("account.period").browse(cr,uid,period_id)
			val.update({
				'date_start':period.date_start,
				'date_end':period.date_stop,
				})
		return {'value':val}

	def export_files(self,cr,uid,ids,context=None):
		if not context:context={}
		wizard = self.browse(cr,uid,ids,context)[0]
		datas = {
			'ids': context.get('active_ids',[]),
			'model': 'efaktur.wizard',
			'filter_by': wizard.filter_by,
			'date_start' : wizard.date_start or False,
			'date_end' : wizard.date_end or False,
			'sale_type' : wizard.sale_type or 'out',
			'goods_type': wizard.goods_type or 'finish',
			'period_id' : wizard.period_id and wizard.period_id.id or False,
			'tax_code':[x.id for x in wizard.tax_code],
			'type':wizard.type,
			'force_period':wizard.force_period and wizard.force_period.id or False,
			'use_force_period':wizard.use_force_period,
			'type_data': wizard.type_data,
			"invoice_ids": [x.id for x in wizard.invoice_ids],
			"efaktur_heads_exception": [x.id for x in wizard.efaktur_heads_exception],
			"efaktur_heads_forced": [x.id for x in wizard.efaktur_heads_forced],
			}
		if datas.get('type_data','import')=='import':
			return {
					'type': 'ir.actions.report.xml',
					'report_name': 'efaktur.wizard.import.%s'%(datas.get('type','out')),
					'report_type': 'webkit',
					'datas': datas,
					}
		elif datas.get('type_data',False)=='spt_masa_1111':
			return {
					'type': 'ir.actions.report.xml',
					'report_name': 'spt.masa.111',
					'report_type': 'webkit',
					'datas': datas,
					}