from osv import osv, fields
from tools.translate import _
import openerp.addons.decimal_precision as dp
import netsvc

class partner(osv.osv):
	_inherit = "res.partner"
	_columns = {
		'advance_in_account_id' : fields.many2one('account.account','Advance Receiveble Account'),
		'advance_out_account_id' : fields.many2one('account.account','Advance Payable Account'),
	}
partner()