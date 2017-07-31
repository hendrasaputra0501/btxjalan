# -*- coding: utf-8 -*-
##############################################################################
#
#	OpenERP, Open Source Management Solution
#	Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU Affero General Public License as
#	published by the Free Software Foundation, either version 3 of the
#	License, or (at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU Affero General Public License for more details.
#
#	You should have received a copy of the GNU Affero General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time

from openerp.osv import fields, osv
from openerp.tools.translate import _

class import_account_bank_loan(osv.osv_memory):
	_name = "import.account.bank.loan"
	_columns = {
		'line_ids': fields.many2many('account.bank.loan', 'account_bank_loan_rel_wizard', 'laon_id', 'wizard_id', 'Bank Loans'),
	}

	def populate_statement(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		drawdown_id = context.get('drawdown_id', False)
		if not drawdown_id:
			return {'type': 'ir.actions.act_window_close'}
		data =  self.read(cr, uid, ids, context=context)[0]
		line_ids = data['line_ids']
		if not line_ids:
			return {'type': 'ir.actions.act_window_close'}
		loan_obj = self.pool.get('account.bank.loan')
		drawdown_obj = self.pool.get('account.bank.loan.drawdown.repayment')
		drawdown_line_obj = self.pool.get('account.bank.loan.drawdown.repayment.line')
		currency_obj = self.pool.get('res.currency')

		drawdown = drawdown_obj.browse(cr, uid, drawdown_id, context=context)
		company_currency = drawdown.company_id.currency_id.id
		curr_currency_id = drawdown.journal_id.currency and drawdown.journal_id.currency.id or company_currency
		current_loan_ids = [x.loan_id.id for x in drawdown.line_ids if x.loan_id]
		ctx = context.copy()
		ctx.update({'date':drawdown.date!=False and drawdown.date or time.strftime('%Y-%m-%d')})
		# for each selected loans
		for line in loan_obj.browse(cr, uid, sorted([loan_id for loan_id in line_ids if loan_id not in current_loan_ids]), context=context):
			if line.liability_move_line_id.currency_id and curr_currency_id == line.liability_move_line_id.currency_id.id:
				amount_original = abs(line.liability_move_line_id.amount_currency)
				amount_unreconciled = abs(line.liability_move_line_id.amount_residual_currency)
			else:
				amount_original = currency_obj.compute(cr, uid, company_currency, curr_currency_id, line.liability_move_line_id.credit or line.liability_move_line_id.debit or 0.0, context=ctx)
				amount_unreconciled = currency_obj.compute(cr, uid, company_currency, curr_currency_id, abs(line.liability_move_line_id.amount_residual), context=ctx)
			
			if amount_unreconciled<=0:
				continue
			
			drawdown_line_obj.create(cr, uid, {
				'loan_id': line.id or False,
				'liability_move_line_id': line.liability_move_line_id and line.liability_move_line_id.id or False,
				'amount_original': amount_original,
				'amount_unreconciled': amount_unreconciled,
				'repayment_id': drawdown_id,
				'date': line.liability_move_line_id.date,
			}, context=context)
		return {'type': 'ir.actions.act_window_close'}

import_account_bank_loan()


class import_account_bank_loan_interest(osv.osv_memory):
	_name = "import.account.bank.loan.interest"
	_columns = {
		'line_ids': fields.many2many('account.bank.loan', 'account_bank_loan_rel_wizard_interest', 'loan_id', 'wizard_id', 'Bank Loans'),
	}

	def populate_statement(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		drawdown_id = context.get('drawdown_id', False)
		if not drawdown_id:
			return {'type': 'ir.actions.act_window_close'}
		data =  self.read(cr, uid, ids, context=context)[0]
		line_ids = data['line_ids']
		if not line_ids:
			return {'type': 'ir.actions.act_window_close'}
		loan_obj = self.pool.get('account.bank.loan')
		drawdown_obj = self.pool.get('account.bank.loan.drawdown.interest')
		interest_line_obj = self.pool.get('account.bank.loan.interest')
		
		drawdown = drawdown_obj.browse(cr, uid, drawdown_id, context=context)
		current_loan_ids = [x.loan_id.id for x in drawdown.line_ids if x.loan_id]
		# for each selected loans
		for line in loan_obj.browse(cr, uid, sorted([loan_id for loan_id in line_ids if loan_id not in current_loan_ids]), context=context):
			interest_line_obj.create(cr, uid, {
				'loan_id': line.id or False,
				'drawdown_interest_id': drawdown.id,
				'date_from': drawdown.date_from,
				'date_to': drawdown.date_to,
				'compute_type': drawdown.compute_type,
				'payment_date' : drawdown.date,
			}, context=context)

		return {'type': 'ir.actions.act_window_close'}

import_account_bank_loan_interest()

class import_account_bank_loan_interest_provision(osv.osv_memory):
	_name = "import.account.bank.loan.interest.provision"
	_columns = {
		'line_ids': fields.many2many('account.bank.loan', 'account_bank_loan_rel_wizard_interest_prov', 'loan_id', 'wizard_id', 'Bank Loans'),
	}

	def populate_statement(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		drawdown_id = context.get('drawdown_id', False)
		if not drawdown_id:
			return {'type': 'ir.actions.act_window_close'}
		data =  self.read(cr, uid, ids, context=context)[0]
		line_ids = data['line_ids']
		if not line_ids:
			return {'type': 'ir.actions.act_window_close'}
		loan_obj = self.pool.get('account.bank.loan')
		drawdown_obj = self.pool.get('account.bank.loan.drawdown.interest')
		interest_line_obj = self.pool.get('account.bank.loan.interest')
		
		drawdown = drawdown_obj.browse(cr, uid, drawdown_id, context=context)
		current_loan_ids = [x.loan_id.id for x in drawdown.line_prov_ids if x.loan_id]
		# for each selected loans
		for line in loan_obj.browse(cr, uid, sorted([loan_id for loan_id in line_ids if loan_id not in current_loan_ids]), context=context):
			int_ids = interest_line_obj.search(cr, uid, [('loan_id','=',line.id),('is_provision','=',True),('state','=','provision')], context=context)
			if int_ids:
				interest_line_obj.write(cr, uid, int_ids, {'drawdown_interest_prov_id':drawdown.id})
		return {'type': 'ir.actions.act_window_close'}

import_account_bank_loan_interest_provision()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
