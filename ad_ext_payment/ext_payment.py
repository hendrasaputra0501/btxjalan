import time
from datetime import datetime
from operator import itemgetter

import netsvc
from osv import fields, osv
from tools.translate import _
import decimal_precision as dp
import tools
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class ext_payment(osv.osv):
    _name = "ext.payment"
    _description = "Extra Payment"
    
    def _amount_total(self, cr, uid, ids, name, args, context=None):
        result = {}
        for ext in self.browse(cr, uid, ids, context=context):
            result[ext.id] = 0.0
            for line in ext.ext_line:
                result[ext.id] = result[ext.id] + line.credit
            #print "line.credit", line.credit, amount_total
        return result
    
    _columns = {
            'name' : fields.char('Transaction', 64,),
            'ext_line' : fields.one2many('ext.payment.line', 'ext_payment_id','Lines', required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'journal_id': fields.many2one('account.journal', 'Journal', required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'ref': fields.char('Reference', size=64, readonly=True, states={'draft':[('readonly',False)]}),
            'date': fields.date('Transaction Date', required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'state':fields.selection([('draft','Draft'), ('approve','Approve')], 'State', readonly=True),
            'move_id':fields.many2one('account.move', 'Account Entry',readonly=True, states={'draft':[('readonly',False)]}),
            'move_ids': fields.related('move_id','line_id', type='one2many', relation='account.move.line', string='Journal Items',readonly=True, states={'draft':[('readonly',False)]}),
            'currency_id':fields.many2one('res.currency', 'Currency', readonly=False),
            'force_period': fields.many2one('account.period','Force Period', required=False, readonly=True, states={'draft':[('readonly',False),('required',True)]}),
            'amount_total'       : fields.function(_amount_total, method=True, string='Total', digits_compute=dp.get_precision('Account'), help="Total"),
            'partner_id':fields.many2one('res.partner', 'Partner', ),
                }
    
    _defaults = {
            'name' : '/',
            'state' : 'draft',
#             'currency_id': 12
                 }
    
    def approve(self, cr, uid, ids, context=None):
        if not context:
            context={}
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        seq_obj = self.pool.get('ir.sequence')
        
        for ext_pay in self.browse(cr, uid, ids, context=context):
            #print "Name===============>>",ext_pay.name
            if ext_pay.name == '/':
                cd = {'date':datetime.strptime(ext_pay.date,DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
                seq = seq_obj.get_id(cr, uid, ext_pay.journal_id.sequence_id.id, context=cd)
            else:
                seq = ext_pay.name
            move = {
                'name': seq,
                'journal_id': ext_pay.journal_id.id,
                'narration': ext_pay.ref,
                'date': ext_pay.date,
                'ref': ext_pay.ref or seq,
                'period_id': ext_pay.force_period.id,
                'partner_id': ext_pay.partner_id.id
                }
            move_id = move_pool.create(cr, uid, move)
            print "LINES :::::", ext_pay.ext_line
            for ext_pay_line in ext_pay.ext_line:
                move_line = {
                    'name': seq or '/',
                    'debit': ext_pay_line.debit,
                    'credit': ext_pay_line.credit,
                    'account_id': ext_pay_line.account_id.id,
                    'move_id': move_id,
                    'journal_id': ext_pay.journal_id.id,
                    'period_id': ext_pay.force_period.id,
                    'partner_id': ext_pay.partner_id.id,
                    #'currency_id': 13,
                    #'amount_currency': company_currency <> current_currency and -bts.amount or 0.0,
                    'date': ext_pay.date,
                }
            #print "1",move_line1
                move_line_pool.create(cr, uid, move_line)
            move_pool.post(cr, uid, [move_id], context={})
            self.write(cr, uid, ids, {
                'state': 'approve',
            })
        return self.write(cr, uid, ids, {'name':seq,'state':'approve','move_id':move_id}, context=context)
    
    
    def cancel_transaction(self, cr, uid, ids, context=None):
        #print "cancel ids",ids
        move_pool = self.pool.get('account.move')
        id=self.browse(cr,uid,ids,context=context)[0]
        move_id=id.move_id.id
        #print "move_id",move_id
        move_pool.write(cr,uid,[move_id],{'state':'draft'})
        move_pool.unlink(cr,uid,[move_id])
        return self.write(cr, uid, ids, {'state':'draft'}, context=context)
    
    
    
ext_payment()

class ext_payment_line(osv.osv):
    _name = "ext.payment.line"
    _description = "Extra Payment"
    
    _columns = {
            'name' : fields.char('Transaction', 64, ),
            'ext_payment_id': fields.many2one('ext.payment', 'Extra Payment ID'),
            'debit': fields.float('Debit'),
            'credit': fields.float('Credit'),
            'account_id' : fields.many2one('account.account', 'Account', required=True),
                }
    
   
ext_payment_line()

