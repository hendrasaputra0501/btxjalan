from osv import osv, fields
from tools.translate import _
from openerp.osv import fields, osv, expression
import openerp.addons.decimal_precision as dp
import netsvc

class label_print(osv.Model):
	_name ="label.print"
	_columns=	{
		'key'	:	fields.char('Key',size=100, required=True),
		'name'	:	fields.char('value',size=100, required=True),
	}