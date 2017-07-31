from openerp.osv import fields,osv

class price_discount(osv.Model):
	_name = "price.discount"
	_rec_name="discount_amt"
	_columns = {
		"discount_amt": fields.float("Discount",required=True),
		'type': fields.selection([('percentage','Percentage'),('fixed','Fixed')],"Discount Type",required=True),
	}
	_defaults = {
	"type":lambda *a:'percentage',
	"discount_amt": lambda *a: 0.0
	}

	def name_get(self, cr, uid, ids, context=None):
		if not ids:
			return []
		if isinstance(ids, (int, long)):
					ids = [ids]
		reads = self.read(cr, uid, ids, ['discount_amt', 'type'], context=context)
		res = []
		for record in reads:
			if record['discount_amt'] and record['type']=='percentage':
				name = str(record['discount_amt'])+'%'
			else:
				name = str(record['discount_amt'])
			res.append((record['id'], name))
		return res

	def compute_discounts(self, cr, uid, ids, base_price, base_qty, context=None):
		if not context:
			context={}
		res = {
			'base_price':base_price,
			'discounts':False,
			'discount_amt':False,
			'total_discount':False,
			'price_after':base_price,
		}
		discounts = []
		discount_amt = []
		total_discount = 0.0
		# n=0
		# price_after = base_price
		# for disc in self.browse(cr,uid,ids,context=context):
		# 	if n==0:
		# 		if disc.type=='percentage':
		# 			discount_x = base_price * disc.discount_amt /100.0
		# 			discount_y = disc.discount_amt
		# 		else:
		# 			discount_x = disc.discount_amt
		# 			discount_y = disc.discount_amt
		# 		n+=1
		# 	else:
		# 		if disc.type=='percentage':
		# 			discount_x = price_after * disc.discount_amt /100.0
		# 			discount_y = disc.discount_amt
		# 		else:
		# 			discount_x = disc.discount_amt
		# 			discount_y = disc.discount_amt
		# 			n+=1
			
		# 	discounts.append(discount_y)
		# 	discount_amt.append(discount_x)
		# 	total_discount +=  discount_x
		# 	price_after -= discount_x
		gross_amount = base_price * base_qty
		for disc in self.browse(cr, uid, ids, context=context):
			if disc.type == 'percentage':
				disc_amt = gross_amount * disc.discount_amt / 100.0
			else:
				disc_amt = disc.discount_amt
			gross_amount -= disc_amt
			total_discount += disc_amt
			discount_amt.append(disc_amt)
			discounts.append(disc.discount_amt)
		try:
			price_after = gross_amount/base_qty
		except:
			price_after = 0.0
		res.update({
			'discounts': discounts,
			'discount_amt': discount_amt,
			'total_discount': total_discount,
			'price_after': price_after
			})
		return res