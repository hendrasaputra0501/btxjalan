from openerp.osv import fields,osv
from datetime import datetime
year_selection = [(num, str(num)) for num in range(1970, (datetime.now().year)+1 )]
import re
class product_catalogue(osv.Model):
	_name = "product.catalogue"
	_rec_name = "catalogue"
	_columns = {
		# "product_id" : fields.many2one('product.product','Reference Product',required=True),
		"from_year" : fields.selection(year_selection, 'From Year',required=True),
		"to_year" : fields.selection(year_selection, 'To Year',required=False),
		"catalogue" : fields.char("Catalogue Number",size=20,required=True),
		"machine_number": fields.char("Machine Number",size=120),
		# "part_number" : fields.char("Part Number",size=20,required=True),
	}

	def name_get(self, cr, uid, ids, context=None):
		if not ids:
			return []
		reads = self.read(cr, uid, ids, ['catalogue'], context)
		res = []
		for record in reads:
			name = str(record['catalogue']) or str(record['id'])
			res.append((record['id'], name))
		return res



class product_catalogue_part_history(osv.Model):
	_name = "product.catalogue.part.history"
	_columns = {
		"catalogue"	: fields.many2one("product.catalogue","Catalogue Number"),
		"from_year"	: fields.related('catalogue','from_year',type='selection',selection=year_selection,string='From Year', store=True, readonly=True),
		"to_year"	: fields.related('catalogue','to_year',type='selection',selection=year_selection,string='To Year', store=True, readonly=True),
		"part_number" : fields.char("Part Number",size=60,required=True),
		"product_id": fields.many2one("product.product","Product",required=True),
	}
	_order = "from_year desc, to_year desc, id desc"

	def onchange_catalogue(self,cr,uid,ids,catalogue,context=None):
		if not context:
			context={}
		val = {}
		if catalogue:
			cat = self.pool.get("product.catalogue").browse(cr,uid,catalogue,context=context)
			val.update({
				"from_year"	: cat.from_year or False,
				"to_year"	: cat.to_year or False,
				})
		return {"value":val}
class product_product(osv.Model):
	_inherit = "product.product"

	def price_info(self,cr,uid,ids,context=None):
		if not context:context={}
		res = {}
		
		for xid in ids:
			res[xid]={
				'max_price':0.0,
				'max_order_id':False,
				'max_partner_id':False,
				'max_date_order':False,
				'last_price':0.0,
				'last_order_id':False,
				'last_partner_id':False,
				'last_date_order':False,
				'min_price':0.0,
				'min_order_id':False,
				'min_partner_id':False,
				'min_date_order':False,
				}
		additional=""" """
		purchase_type=""" """
		date_order=""" """

		if ids and len(ids)>0:
			additional = """a.product_id in ("""
			for x in ids:
				additional+=str(x)+","
			additional=additional[:-1]+")"
		
		if context.get('purchase_type',False):
			purchase_type = """and b.purchase_type is not NULL and b.purchase_type="""
			purchase_type += "'"+str(context.get('purchase_type',False))+"'"

		if context.get('date_order',False):
			date_order = """and b.date_order<="""
			date_order += "'"+context.get('date_order',False)+"'"
		# print "=============",additional
		cr.execute("""
			select distinct on (a.product_id) 
			round(a.price_unit /(select x.rate from res_currency_rate x where x.name < b.date_order and x.currency_id=c.currency_id order by x.name desc,x.id desc limit 1)::numeric,2 ) as price_unit_usd,
			a.price_unit, a.product_id,a.order_id,a.partner_id,b.date_order,b.id
			from purchase_order_line a 
			left join purchase_order b on a.order_id=b.id
			left join product_pricelist c on b.pricelist_id=c.id

			where 
			"""+additional+"""
			"""+purchase_type+"""
			"""+date_order+"""
			and a.state not in ('draft','sent','cancel')
			order by product_id asc, price_unit desc,date_order desc,id desc""")
		query_max = cr.dictfetchall()
		for x in query_max:
			res[x['product_id']].update({
				'max_price':x['price_unit'],
				'max_order_id':x['order_id'],
				'max_partner_id':x['partner_id'],
				'max_date_order':x['date_order'],
				})
		cr.execute("""
			select distinct on (a.product_id) 
			round(a.price_unit /(select x.rate from res_currency_rate x where x.name < b.date_order and x.currency_id=c.currency_id order by x.name desc,x.id desc limit 1)::numeric,2 ) as price_unit_usd,
			a.price_unit, a.product_id,a.order_id,a.partner_id,b.date_order,b.id
			from purchase_order_line a 
			left join purchase_order b on a.order_id=b.id
			left join product_pricelist c on b.pricelist_id=c.id

			where 
			"""+additional+"""
			"""+purchase_type+"""
			"""+date_order+"""
			and a.state not in ('draft','sent','cancel')
			order by product_id asc, price_unit asc,date_order desc,id desc""")
		query_min = cr.dictfetchall()
		for y in query_min:
			res[y['product_id']].update({
				'min_price':y['price_unit'],
				'min_order_id':y['order_id'],
				'min_partner_id':y['partner_id'],
				'min_date_order':y['date_order'],
				})
		cr.execute("""
			select distinct on (a.product_id) 
			round(a.price_unit /(select x.rate from res_currency_rate x where x.name < b.date_order and x.currency_id=c.currency_id order by x.name desc,x.id desc limit 1)::numeric,2 ) as price_unit_usd,
			a.price_unit, a.product_id,a.order_id,a.partner_id,b.date_order,b.id,
			round(a.price_unit-(a.price_unit*(coalesce(disc_po.discount_amt,0)/100))::numeric,4) as price_after_discount
			from purchase_order_line a 
			left join purchase_order b on a.order_id=b.id
			left join product_pricelist c on b.pricelist_id=c.id
			LEFT JOIN ( 
						select pdpol_rel.po_line_id,pd.discount_amt from price_discount_po_line_rel pdpol_rel
						inner join price_discount pd on pdpol_rel.disc_id=pd.id
				)disc_po on disc_po.po_line_id=a.id
			where 
			"""+additional+"""
			"""+purchase_type+"""
			"""+date_order+"""
			and a.state not in ('draft','sent','cancel')
			order by product_id asc, date_order desc,id desc,price_unit desc
			""")
		query_last = cr.dictfetchall()
		for z in query_last:
			z['product_id']
			res[z['product_id']].update({
				'last_price':z['price_after_discount'],
				# 'last_price':z['price_unit'],
				'last_order_id':z['order_id'],
				'last_partner_id':z['partner_id'],
				'last_date_order':z['date_order'],
				})
		return res
			

	def _get_price_info(self, cr, uid, ids, field_names=None, arg=False, context=None):
		if not field_names:
			field_names = []
		if context is None:
			context = {}
		res = {}
		for id in ids:
			res[id] = {}.fromkeys(field_names, 0.0)
		fetch = self.price_info(cr,uid,ids,context=context)
		for f in field_names:
			res[id][f]= fetch[id][f]
		return res

	def _get_catalogue_numbers(self, cr, uid, ids, field_names, arg=None, context=None):
		result = {}
		if not ids: return result
		
		for product in self.browse(cr,uid,ids):
			result[product.id] = {
				'catalogue_numbers': '',
				'part_numbers': '',
				'catalogue_number_id':False,
				'part_number_id':False,
			}
			
			for cat in product.catalogue_lines:
				cat_nbr = cat.catalogue and str(cat.catalogue.catalogue) or False
				part_nbr = cat.part_number and cat.part_number not in (False,'') and str(cat.part_number) or False
				result[product.id]['catalogue_numbers']+= cat_nbr and cat_nbr+'; ' or ''
				result[product.id]['part_numbers']+=part_nbr and part_nbr + '; ' or ''
			result[product.id]['catalogue_number_id']=product.catalogue_lines and product.catalogue_lines[0] and product.catalogue_lines[0].catalogue and product.catalogue_lines[0].catalogue.id or False,
			result[product.id]['part_number']=product.catalogue_lines and product.catalogue_lines[0] and product.catalogue_lines[0].part_number or False
		return result

	# def _product_partner_ref(self, cr, uid, ids, name, arg, context=None):
 #        res = {}
 #        if context is None:
 #            context = {}
 #        for p in self.browse(cr, uid, ids, context=context):
 #            data = self._get_partner_code_name(cr, uid, [], p, context.get('partner_id', None), context=context)
 #            if not data['variants']:
 #                data['variants'] = p.variants
 #            if not data['code']:
 #                data['code'] = p.code
 #            if not data['name']:
 #                data['name'] = p.name
 #            res[p.id] = (data['code'] and ('['+data['code']+'] ') or '') + \
 #                    (data['name'] or '') + (data['variants'] and (' - '+data['variants']) or '')
 #        return res

	_columns = {
		"first_segment_code" : fields.many2one('product.first.segment.code', 'Segment Code 1', required=False),
		"second_segment_code" : fields.many2one('product.second.segment.code', 'Segment Code 2', required=False),
		"third_segment_code" : fields.char('Segment Code 3', size=10, required=False),
		"quality_code" : fields.char('Quality Code', size=20, required=False),
		"dimension_code" : fields.char('Dimension Code', size=20, required=False),
		"catalogue_lines" : fields.one2many('product.catalogue.part.history','product_id','Catalogue Lines'),
		"catalogue_numbers" : fields.function(_get_catalogue_numbers, type='char', string='Catalogue Numbers', method=True,
			store={
				'product.product':(lambda self,cr,uid,ids,context={}:ids,['catalogue_lines'],10),
			}, multi="all_catalogue"),
		"catalogue_number_id" : fields.function(_get_catalogue_numbers, type='many2one',relation="product.catalogue", string='Catalogue Number ID', method=True,
			store={
				'product.product':(lambda self,cr,uid,ids,context={}:ids,['catalogue_lines'],10),
			}, multi="all_catalogue"),
		"part_numbers" : fields.function(_get_catalogue_numbers, type='char', string='Part Numbers', method=True,
			store={
				'product.product':(lambda self,cr,uid,ids,context={}:ids,['catalogue_lines'],10),
			}, multi="all_catalogue"),
		"part_number" : fields.function(_get_catalogue_numbers, type='char',size=60, string='Part Number ID', method=True,
			store={
				'product.product':(lambda self,cr,uid,ids,context={}:ids,['catalogue_lines'],10),
			}, multi="all_catalogue"),
		"last_price" 		: fields.function(_get_price_info,type="float",multi='fetch_info',string="Latest Purchase Price",),
		"last_order_id"		: fields.function(_get_price_info,type="many2one",relation="purchase.order",multi='fetch_info',string="Latest PO",),
		"last_partner_id"	: fields.function(_get_price_info,type="many2one",relation="res.partner",multi='fetch_info',string="Latest Vendor",),
		"last_date_order"	: fields.function(_get_price_info,type="date",multi='fetch_info',string="Latest Purchase Date",),
		"min_price" 		: fields.function(_get_price_info,type="float",multi='fetch_info',string="Min. Purchase Price",),
		"min_order_id"		: fields.function(_get_price_info,type="many2one",relation="purchase.order",multi='fetch_info',string="Min. PO",),
		"min_partner_id"	: fields.function(_get_price_info,type="many2one",relation="res.partner",multi='fetch_info',string="Min. Vendor",),
		"min_date_order"	: fields.function(_get_price_info,type="date",multi='fetch_info',string="Min. Purchase Date",),
		"max_price" 		: fields.function(_get_price_info,type="float",multi='fetch_info',string="Max. Purchase Price",),
		"max_order_id"		: fields.function(_get_price_info,type="many2one",relation="purchase.order",multi='fetch_info',string="Max. PO",),
		"max_partner_id"	: fields.function(_get_price_info,type="many2one",relation="res.partner",multi='fetch_info',string="Max. Vendor",),
		"max_date_order"	: fields.function(_get_price_info,type="date",multi='fetch_info',string="Max. Purchase Date",),
	}

	def onchange_segment_code(self, cr, uid, ids, internal_type, first_segment_code, second_segment_code, third_segment_code,name,dimension_code,quality_code,context=None):
		if not context:context={}
		first_segment_obj = self.pool.get('product.first.segment.code')
		second_segment_obj = self.pool.get('product.second.segment.code')

		if not internal_type:
			return {'value':{}}

		first_code = ""
		if first_segment_code:
			first_code = first_segment_obj.browse(cr, uid, first_segment_code).code

		second_code = ""
		next=''
		if second_segment_code:
			second_code = second_segment_obj.browse(cr, uid, second_segment_code).code
		first_letter=False
		if name:
			x=re.search(r"[A-Z,a-z]",name)
			first_letter = x.group(0)
		else:
			first_letter=''
		if first_segment_code and second_segment_code and first_letter:
			cr_fetch = False
			if context.get('active_id',False):
				prod = self.browse(cr,uid,context.get('active_id',False))
				curr_first_seg = prod.first_segment_code and prod.first_segment_code or False
				curr_second_seg = prod.second_segment_code and prod.second_segment_code or False
				curr_third_seg = prod.third_segment_code
				c1 = curr_first_seg==first_segment_code or False
				c2 = curr_second_seg==second_segment_code or False
				c3 = curr_third_seg==third_segment_code or False
				
				if c1 and c2:
					next =curr_third_seg
				else:
					cr.execute("select max(CASE WHEN (select(right(substring(code.default_code from 7 for (char_length(code.default_code)-6)),-1) ~ '^[0-9]+$')) \
								THEN right(substring(code.default_code from 7 for (char_length(code.default_code)-6)),-1)::int \
								ELSE 0 END) \
								from (select default_code from product_product where internal_type=%s and first_segment_code=%s \
								and second_segment_code=%s and third_segment_code like %s and id <> %s) code",
								(internal_type, first_segment_code,second_segment_code,first_letter+'%',context.get('active_id',False)))
					cr_fetch = cr.fetchone()[0]
			else:
				cr.execute("select max(CASE WHEN (select(right(substring(code.default_code from 7 for (char_length(code.default_code)-6)),-1) ~ '^[0-9]+$')) \
							THEN right(substring(code.default_code from 7 for (char_length(code.default_code)-6)),-1)::int \
							ELSE 0 END) \
							from (select default_code from product_product where internal_type=%s and first_segment_code=%s and second_segment_code=%s \
							and third_segment_code like %s) code",
							(internal_type, first_segment_code,second_segment_code,first_letter+'%'))

				cr_fetch = cr.fetchone()[0]
			if cr_fetch:
				next = first_letter+((5-len(str(cr_fetch+1)))*'0')+str(cr_fetch+1)
			elif not next:
				next = first_letter+'00001'

		if not first_code and not second_code and not third_segment_code:
			res = {}
		else:
			res={
				'default_code':(first_code or '')+(second_code or '')+(third_segment_code or ''),
				'third_segment_code':next
				}
		return {'value':res}

class product_undefined_info(osv.osv):
	_name = "product.undefined.info"
	_columns = {
		"name"			: fields.char("Description",size=128),
		"product_id" 	: fields.many2one('product.product',"Product",required=True),
		"po_number"		: fields.char("Last PO",required=True),
		"po_date"		: fields.date("Last PO Date",required=True),
		"partner_id"	: fields.many2one("res.partner","Vendor",required=False),
		"partner_name"	: fields.char("Vendor Name",required=True),
		"currency_id"	: fields.many2one("res.currency","Currency",required=True),
		"price_unit"	: fields.float("Price Unit",required=True,digits=(16,2)),
	}
