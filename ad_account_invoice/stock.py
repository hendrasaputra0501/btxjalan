from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
from openerp.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)


class stock_picking(osv.osv):
	
	_inherit = "stock.picking"

	def get_additional_addrs_from_shipping_instruction(self, cr, uid, picking, context=None):
		result = {}

		result.update({
			# 'shipper' : picking.container_book_id and picking.container_book_id.shipper and picking.container_book_id.consignee.id or False,
			'show_shipper_address' : picking.container_book_id and picking.container_book_id.show_shipper_address,
			's_address_text' : picking.container_book_id and picking.container_book_id.s_address_text,

			'buyer' : picking.sale_id and picking.sale_id.partner_id.id or False,
			'show_buyer_address' : False,
			'address_text' : '',
			
			'consignee' : picking.container_book_id and picking.container_book_id.consignee and picking.container_book_id.consignee.id or False,
			'show_consignee_address' : picking.container_book_id and picking.container_book_id.show_consignee_address,
			'c_address_text' : picking.container_book_id and picking.container_book_id.c_address_text,
			
			'notify' : picking.container_book_id and picking.container_book_id.notify_party and picking.container_book_id.notify_party.id or False,
			'show_notify_address' : picking.container_book_id and picking.container_book_id.show_notify_address,
			'n_address_text' : picking.container_book_id and picking.container_book_id.n_address_text,
			
			'applicant' : picking.container_book_id and picking.container_book_id.applicant and picking.container_book_id.applicant.id or False,
			'show_applicant_address' : picking.container_book_id and picking.container_book_id.show_applicant_address,
			'a_address_text' : picking.container_book_id and picking.container_book_id.a_address_text,
		})

		return result
	
	def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):
		""" Builds the dict containing the values for the invoice
			@param picking: picking object
			@param partner: object of the partner to invoice
			@param inv_type: type of the invoice ('out_invoice', 'in_invoice', ...)
			@param journal_id: ID of the accounting journal
			@return: dict that will be used to create the invoice object
		"""
		invoice_vals = super(stock_picking, self)._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
		
		invoice_vals.update(self.get_additional_addrs_from_shipping_instruction(cr, uid, picking))
		
		return invoice_vals	