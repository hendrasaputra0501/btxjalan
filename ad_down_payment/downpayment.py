import time
from datetime import datetime
from operator import itemgetter

import netsvc
from osv import fields, osv
from tools.translate import _
import decimal_precision as dp
import tools

class downpayment(osv.osv):
    _name = 'downpayment'
    _description = 'Downpayment'
    
    def _compute_total(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for dp in self.browse(cr, uid, ids):
            tot = 0.0
            for line in dp.dp_line:
                amount = line.amount
                tot += amount
        
            res[dp.id] = {
                'amount_dp_total': tot,
                        }
            
        return res
    
    _columns = {
            'name' : fields.char('Transaction', 64, ),
            'dp_line' : fields.one2many('downpayment.line', 'dp_id', 'Lines',readonly=True, states={'draft':[('readonly', False)]}),
            'journal_id': fields.many2one('account.journal', 'Journal'),
            'ref': fields.char('Reference', 64, readonly=True, states={'draft':[('readonly', False)]}),
            'date': fields.date('Transaction Date', required=True, readonly=True, states={'draft':[('readonly', False)]}),
            'payment_date': fields.date('Payment Date',),
            'state':fields.selection([('draft', 'Draft'), ('confirm', 'Waiting CFO Approve'), ('approve', 'Waiting Treasury Approve'), ('approve2', 'DONE'), ('cancel', 'Cancel')], 'State', readonly=True),
            'move_id':fields.many2one('account.move', 'Account Entry', readonly=True, states={'draft':[('readonly', False)]}),
            'move_ids': fields.related('move_id', 'line_id', type='one2many', relation='account.move.line', string='Journal Items', readonly=True, states={'draft':[('readonly', False)]}),
            'currency_id':fields.many2one('res.currency', 'Currency', readonly=False),
            'force_period': fields.many2one('account.period', 'Force Period', required=False, readonly=True, states={'draft':[('readonly', False), ('required', False)]}),
            'used': fields.boolean('Used'),
            'partner_id': fields.many2one('res.partner', 'Partner', change_default=1, required=True ,readonly=True, states={'draft':[('readonly',False)]}),
            'downpayment_used'      : fields.float('Used'),
            'company_id'    : fields.many2one('res.company', 'Company', ),
            #############################################
            'payment_adm': fields.selection([
                ('cash','Cash'),
                ('free_transfer','Non Payment Administration Transfer'),
                ('transfer','Transfer'),
                #('cheque','Cheque'),
                ],'Payment Adm', readonly=True, select=True, states={'approve': [('readonly', False)]}),
            'adm_acc_id': fields.many2one('account.account', 'Account Adm', readonly=True, states={'approve': [('readonly', False)]}),
            'adm_comment': fields.char('Comment Adm', size=128, required=False, readonly=True, states={'approve': [('readonly', False)]}),
            'adm_amount': fields.float('Amount Adm', readonly=True, states={'approve': [('readonly', False)]}),
            'bank_id': fields.many2one("res.bank", "Bank", required=False, readonly=True, states={"approve":[("readonly", False)]}, select=2),
            'cheque_number': fields.char('Cheque No', size=128, required=False, readonly=True, states={'approve': [('readonly', False)]}),
            "cheque_start_date": fields.date("Cheque Date", required=False, readonly=True, states={"approve":[("readonly", False)]}),
            "cheque_end_date": fields.date("Cheque Expire Date", required=False, readonly=True, states={"approve":[("readonly", False)]}),
            "amount_dp_total" : fields.function(_compute_total, digits_compute=dp.get_precision('Account'), method=True, string='Total', multi='total', readonly=True),
            ##############################################
                }
    _defaults = {
            'name'          :'/',
            'state'         :'draft',
            'payment_adm'   :"cash",
            'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'cash.advance',context=c),
                 }
    
#    def compute_dp_tax_all(self, cr, uid, taxes, price_unit, quantity, address_id=None, product=None, partner=None):
#        print "aha"
#        """
#        RETURN: {
#                'total': 0.0,                # Total without taxes
#                'total_included: 0.0,        # Total with taxes
#                'taxes': []                  # List of taxes, see compute for the format
#            }
#        """
#        precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
#        totalin = totalex = round(price_unit * quantity, precision)
#        tin = []
#        tex = []
#        for tax in taxes:
#            if tax.price_include:
#                tin.append(tax)
#            else:
#                tex.append(tax)
#        tin = self.compute_inv(cr, uid, tin, price_unit, quantity, address_id=address_id, product=product, partner=partner)
#        for r in tin:
#            totalex -= r.get('amount', 0.0)
#        totlex_qty = 0.0
#        try:
#            totlex_qty=totalex/quantity
#        except:
#            pass
#        tex = self._compute(cr, uid, tex, totlex_qty, quantity, address_id=address_id, product=product, partner=partner)
#        for r in tex:
#            totalin += r.get('amount', 0.0)
#            
#        apa = {
#            'total': totalex,
#            'total_included': totalin,
#            'taxes': tin + tex
#            
#        }
#        print apa
#            
#        return apa

    def compute_tax_dp(self, cr, uid, ids, taxes, amount, journal, account_id, date, period_id, partner_id, move_id, context=None):
        
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        print "Taxes::::", taxes
        print "amount :::", amount
        print "cccccccc", move_id
        taxes_to_paid = 0.0
        print "Context", context
        for tax in taxes:
            name_tax        = tax['name']
            amount_tax      = tax['amount']
            price_include   = tax['price_include']
            type            = tax['type']
            account_tax     = tax['account_collected_id']['id']
            tax_code_id     = tax['tax_code_id']['id']
            
            amount_dp_in_tax = amount * amount_tax
            print "----------------->>", amount_tax, price_include, type, amount_dp_in_tax
            if amount_dp_in_tax < 0:
                print "atas"
                debit   = 0.0
                credit  = abs(amount_dp_in_tax)
                print "Debit", debit, "VS", "Credit", credit
            else:
                "bawah"
                debit   = abs(amount_dp_in_tax)
                credit  = 0.0
                
                print "Debit", debit, "VS", "Credit", credit
            move_line_tax = {
                        'name': name_tax,
                        'account_id': account_tax or account_id,
                        'move_id': move_id,
                        'partner_id': partner_id,
                        'date': date,
                        'period_id' : period_id,
                        'debit': debit,# < 0 and -diff or 0.0,
                        'credit': credit,#diff > 0 and diff or 0.0,
                        'tax_amount' : amount_dp_in_tax,
                        'tax_code_id' : tax_code_id or False,
                        #'currency_id': company_currency <> transaction_currency and transaction_currency or False,
                        #'amount_currency': company_currency <> transaction_currency and sign_adm * -diff_adm or 0.0,
                    }
            move_line_pool.create(cr, uid, move_line_tax)
            taxes_to_paid += amount_dp_in_tax
        print "taxes_to_paid------------>>>??", taxes_to_paid
        #raise osv.except_osv(_('No Retention Account !'),_("You must define a retention account !"))
        return taxes_to_paid
    
    def approve(self, cr, uid, ids, context=None):
        if not context:
            context={}
        for dp in self.browse(cr, uid, ids, context=context):
            context_multi_currency = context.copy()
            #context_multi_currency.update({'date': dp.date})
            context_multi_currency.update({'date': dp.payment_date})
        #print "Context", context, "+++++++++++++", context_multi_currency
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        seq_obj = self.pool.get('ir.sequence')
        currency_pool = self.pool.get('res.currency')
        
        for dp in self.browse(cr, uid, ids, context=context):
            #print "Name===============>>",dp.name
            transaction_currency = dp.currency_id.id
            #print "transaction_currency", transaction_currency
            company_currency = dp.company_id.currency_id.id
            
            if dp.name != '/':
                seq = dp.name
            elif dp.journal_id.sequence_id:
                seq = seq_obj.get_id(cr, uid, dp.journal_id.sequence_id.id)
            else:
                raise osv.except_osv(_('Error !'), _('Please define a sequence on the journal !'))
            
            if dp.ref:
                ref = dp.ref
            else:
                ref = seq
            move = {
                'name': seq,
                'journal_id': dp.journal_id.id,
                'narration': dp.ref,
                'date': dp.payment_date,
                'ref': ref,
                'period_id': dp.force_period.id
                }
            move_id = move_pool.create(cr, uid, move)
            debit_total = 0.0
            tax_to_paid = 0.0
            tax_amount  = 0.0
            for dp_line in dp.dp_line:
                
                
                debit_amount = 0.0
                debit_amount = currency_pool.compute(cr, uid, transaction_currency, company_currency, dp_line.amount, context=context_multi_currency)
                ##################Taxes#########################
                tax_code_id = False
                if dp_line.dp_line_tax_id:
                    tax_amount = debit_amount
                    tax_code_id = dp_line.dp_line_tax_id[0].base_code_id.id
                    print "tax_code_id", tax_code_id
                taxes = dp_line.dp_line_tax_id
                print"taxes", taxes 
                tax_to_paid_comp = self.compute_tax_dp(cr, uid, ids, taxes, debit_amount, dp.journal_id.id, dp_line.account_id.id, dp.payment_date, dp.force_period.id, dp.partner_id.id, move_id)
                tax_to_paid_tax = currency_pool.compute(cr, uid, company_currency, transaction_currency, tax_to_paid_comp, context=context_multi_currency)
                tax_to_paid += tax_to_paid_tax
                print "tax_to_paid---->>", tax_to_paid
                ###########################################
                
                #print "debit_amount------", debit_amount
                move_line = {
                    'name': dp_line.name or '/',
                    #'debit': dp_line.amount,
                    'debit': debit_amount,
                    'credit': 0.0,
                    'account_id': dp_line.account_id.id,
                    'move_id': move_id,
                    'journal_id': dp.journal_id.id,
                    'period_id': dp.force_period.id,
                    'partner_id': dp.partner_id.id,
                    'tax_amount' : tax_amount,
                    'tax_code_id' : tax_code_id,
                    #'currency_id': 13,
                    #'amount_currency': company_currency <> current_currency and -bts.amount or 0.0,
                    'date': dp.payment_date,
                }
                debit = dp_line.amount,
            #print "1",move_line1
                #print "DEbit", debit[0]
                debit_total += debit[0]
                move_line_pool.create(cr, uid, move_line)
                
                self.pool.get('downpayment.line').write(cr, uid, [dp_line.id], {'state': 'paid'})
                print "debit_total", debit_total
            #############TAXES################
            debit_total = debit_total + tax_to_paid
            print "debit_total------>>", debit_total
            #############################
            debit_total = currency_pool.compute(cr, uid, transaction_currency, company_currency, debit_total, context=context_multi_currency)
            move_line_first = {
                    'name': dp_line.name or '/',
                    'debit': 0.0,
                    #'credit': debit_total,
                    'credit': debit_total,
                    'account_id': dp.journal_id.default_credit_account_id.id,
                    'move_id': move_id,
                    'journal_id': dp.journal_id.id,
                    'period_id': dp.force_period.id,
                    'partner_id': dp.partner_id.id,
                    #'currency_id': 13,
                    #'amount_currency': company_currency <> current_currency and -bts.amount or 0.0,
                    'date': dp.payment_date,
                }
            #print "1",move_line1
            move_line_pool.create(cr, uid, move_line_first)
            
            #            #----------------------tambah disini buat gbu-------------
            #print "pppppppppppppppp"
            diff_adm = dp.adm_amount
            if dp.payment_adm == 'transfer' or dp.payment_adm == 'cheque':
                debit_adm = currency_pool.compute(cr, uid, company_currency, company_currency, diff_adm, context=context_multi_currency)
                credit_adm = currency_pool.compute(cr, uid, company_currency, company_currency, diff_adm, context=context_multi_currency)
                sign_adm = debit_adm - credit_adm < 0 and -1 or 1
                if dp.payment_adm == 'transfer':
                    cost_name = dp.adm_comment
                else:
                    cost_name = 'Cheque Fee'
                    
                move_line_adm_c = {
                    'name': cost_name,
                    'account_id': dp.journal_id.default_credit_account_id.id,
                    'move_id': move_id,
                    'partner_id': dp.partner_id.id,
                    'date': dp.payment_date,
                    'debit': 0,# < 0 and -diff or 0.0,
                    'credit': credit_adm,#diff > 0 and diff or 0.0,
                    'currency_id': company_currency <> transaction_currency and transaction_currency or False,
                    'amount_currency': company_currency <> transaction_currency and sign_adm * -diff_adm or 0.0,
                }
                account_id = dp.adm_acc_id.id
                move_line_adm_d = {
                    'name': cost_name,
                    'account_id': account_id,
                    'move_id': move_id,
                    'partner_id': dp.partner_id.id,
                    'date': dp.payment_date,
                    'debit': debit_adm,# < 0 and -diff or 0.0,
                    'credit': 0,#diff > 0 and diff or 0.0,
                    'currency_id': company_currency <> transaction_currency and transaction_currency or False,
                    'amount_currency': company_currency <> transaction_currency and sign_adm * diff_adm or 0.0,
                }
                #print "xxxx3xxxx",move_line_adm_c
                #print "xxxx4xxxx",move_line_adm_d
                if diff_adm != 0:
                    move_line_pool.create(cr, uid, move_line_adm_c)
                    move_line_pool.create(cr, uid, move_line_adm_d)
            #------------------------------------------------------
            
            move_pool.post(cr, uid, [move_id], context={})
            if dp.name == '/':
                self.write(cr, uid, ids, {'name': seq})
            self.write(cr, uid, ids, {
                'state': 'approve2',
            })
        return self.write(cr, uid, ids, {'state':'approve2','move_id':move_id}, context=context)
    
    def cancel_transaction(self, cr, uid, ids, context=None):
        #print "cancel ids",ids
        move_pool = self.pool.get('account.move')
        id = self.browse(cr,uid,ids,context=context)[0]
        move_id=id.move_id.id
        if id.move_ids:
            #print "move_id",move_id
            move_pool.write(cr,uid,[move_id],{'state':'draft'})
            move_pool.unlink(cr,uid,[move_id])
        for line in id.dp_line:
            self.pool.get('downpayment.line').write(cr, uid, line.id, {'state':'draft'}, context=context)
        return self.write(cr, uid, ids, {'state':'cancel'}, context=context)
    
    def action_cancel_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state':'draft'})
        wf_service = netsvc.LocalService("workflow")
        for inv_id in ids:
            wf_service.trg_delete(uid, 'downpayment', inv_id, cr)
            wf_service.trg_create(uid, 'downpayment', inv_id, cr)
        return True
    
downpayment()

class downpayment_line(osv.osv):
    _name = 'downpayment.line'
    _description = 'Downpayment Line'
    _columns = {
            'name'                  : fields.char('Transaction', 64, required=True),
            'dp_id'                 : fields.many2one('downpayment', 'ID'),
            'amount'                : fields.float('Amount'),
            'account_id'            : fields.many2one('account.account', 'Account', required=True),
            'purchase_id'           : fields.many2one('purchase.order', 'Purchase ID', ),
            'state'                 : fields.selection([('draft', 'In Progress'), ('paid', 'Paid')], 'State', readonly=True),
            #################Add Taxes##################
            'dp_line_tax_id'   : fields.many2many('account.tax', 'account_dp_line_tax', 'dp_line_id', 'tax_id', 'Taxes', domain=[('parent_id','=',False)]),
            ############################################
                }
    _defaults = {
            'state' : 'draft',
                 }
downpayment_line()
