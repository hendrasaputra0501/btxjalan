from osv import osv, fields
from tools.translate import _
from openerp.osv import fields, osv, expression
import openerp.addons.decimal_precision as dp
import netsvc

class wizard_change_label(osv.osv_memory):
	_name = "wizard.change.label"
	_columns = {
		'field_ids':fields.one2many('wizard.change.label.line','wizard_id','Fields'),
	}

	def default_get(self, cr, uid, fields_list, context=None):
		"""
		Returns default values for fields
		@param fields_list: list of fields, for which default values are required to be read
		@param context: context arguments, like lang, time zone

		@return: Returns a dict that contains default values for fields
		"""
		res = super(wizard_change_label, self).default_get(cr, uid, fields_list, context=context)
		if context is None:
			context = {}
		lc_id = context.get('active_id',False)
		label_print = eval(context.get('label','{}'))
		if not label_print:
			return res

		domain = [('key','in',label_print.keys())]
		# if context.get('model',False):
		# 	domain.append(('model_id','=',context.get('model',False)))
		field_ids = self.pool.get('label.print').search(cr,uid,domain)
		fx = []
		for field in self.pool.get('label.print').browse(cr,uid,field_ids):
			fx.append({
				'field_id':field.id,
				'label':label_print[field.key]
			})

		if 'field_ids' in fields_list:
			res.update(field_ids=fx)
		
		return res

	def set_label_print(self, cr, uid, ids, context=None):
		if context is None: context = {}
		active_ids = context.get('active_ids', [])
		data = self.read(cr, uid, ids, ['field_ids'])
		if not data:
			return False
		data_line = self.pool.get('wizard.change.label.line').browse(cr, uid, data[0].get('field_ids',[]))
		if not data_line:
			return False
		result={}
		for line in data_line:
			result.update({line.field_id.key.encode("utf-8"):line.label.encode("utf-8")})
		self.pool.get('letterofcredit').write(cr,uid,context['active_id'],{'label_print':str(result)})
		return True

wizard_change_label()

class wizard_change_label_line(osv.osv_memory):
	_name = "wizard.change.label.line"
	_rec_name ="field_id"
	_columns = {
		'field_id':fields.many2one('label.print','name'),
		'label':fields.char('Label',size=100),
		'wizard_id':fields.many2one('wizard.change.label','Wizard')
	}
wizard_change_label()