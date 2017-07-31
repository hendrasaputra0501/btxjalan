import time
from lxml import etree
import decimal_precision as dp

import netsvc
import pooler
from osv import fields, osv, orm
from tools.translate import _

class budget_info_inv(osv.osv):
    _name = 'budget.info.inv'
    _description = 'Budget Info Supplier Invoice'
    
    def _amount_budget(self, cr, uid, ids, name, args, context=None):
        print "AAAAAAA"
        res={}
        for line in self.browse(cr, uid, ids, context=None):
            account_analytic_id = line.account_analytic_id.id
            #date_end = line.voucher_id.date_end[:4]
            #print "+++++++++++++++++++++++++++", line.cash_advance_id.req_date[:4]
            
            
            date_end = line.invoice_id.date_invoice and line.invoice_id.date_invoice[:4] or False
            #date_end = 2014
            if not date_end:
                return res
            
            #date_from = str(line.period_id.date_start)
            #date_to = str(line.period_id.date_stop)
            #date_from = line.period_id.date_start
            #date_to = line.period_id.date_stop
            #print "+++++++++++++++", account_analytic_id, date_end
            #acc_ids = line.budget_item_id.
            cr.execute("select sum(a.amount) as amount_budget from ad_budget_line a, account_period b "
                       " where a.analytic_account_id = %s and a.period_id = b.id and to_char(b.date_start,'yyyy') = %s ",(str(account_analytic_id),str(date_end),))
#            result = cr.dictfetchone()
#            #print "line.id",line.id
#            if result['amount_budget'] is None:
#                result.update({'amount_budget': 0.0})
#            result.update({'amount_budget':abs(result['amount_budget'])})
#            res.update({line.id:result})
            
            amount = cr.fetchone()
            #print "amount", amount
            amount = amount[0] or 0.00
            res[line['id']] = amount
            print "res", res
        return res
    
    def _amount_spent(self, cr, uid, ids, name, args, context=None):
        res={}
        for line in self.browse(cr, uid, ids, context=None):
            account_analytic_id = line.account_analytic_id.id
            #date_end = line.material_req_id.date_end[:4]
            date_end = line.invoice_id.date_invoice and line.invoice_id.date_invoice[:4] or False
            if not date_end:
                return res
            #acc_ids = line.budget_item_id.
            cr.execute("SELECT SUM(amount) as balance_real FROM account_analytic_line "
                   "WHERE account_id=%s AND to_char(date,'yyyy') = %s ", (str(account_analytic_id),str(date_end),))
            amount_real = cr.fetchone()
            amount_real = amount_real[0] or 0.00
            #print amount_real
            
            cr.execute("select SUM(x.product_qty*x.price_unit) as balance_virtual FROM purchase_order_line x, purchase_order y "
                        " where y.state in ('approved') and x.order_id = y.id "
                        "  and x.account_analytic_id = %s and to_char(x.date_planned,'yyyy') = %s ", (str(account_analytic_id),str(date_end),))
            amount_virtual1 = cr.fetchone()
            amount_virtual1 = amount_virtual1[0] or 0.00
            
            cr.execute("SELECT SUM(a.product_qty*a.price_unit) as balance_virtual FROM purchase_order_line x, purchase_order y, stock_move a "
                     " WHERE x.order_id = y.id and a.purchase_line_id = x.id and a.state in ('cancel','done') and "
                     " x.order_id in (select a.id from purchase_order a, account_invoice b, purchase_invoice_rel c "
                       "  where a.id=c.purchase_id and b.id= c.invoice_id and (a.state in ('approved') and b.state in ('open','paid','cancel')) and a.id=y.id) and "
                       " x.account_analytic_id = %s and to_char(x.date_planned,'yyyy') = %s ",(str(account_analytic_id),str(date_end),))
            amount_virtual2 = cr.fetchone()
            amount_virtual2 = amount_virtual2[0] or 0.00
            res[line['id']] = (amount_virtual1 - amount_virtual2) + abs(amount_real)
        return res
    
    def _amount_current(self, cr, uid, ids, name, args, context=None):
        print "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
        res={}
        for line in self.browse(cr, uid, ids, context=None):
            account_analytic_id = line.account_analytic_id.id
            invoice_id = line.invoice_id.id
            date_end = line.invoice_id.date_invoice and line.invoice_id.date_invoice[:4] or False
            #date_end = 2014
            if not date_end:
                return res
            #acc_ids = line.budget_item_id.
            
            cr.execute("select sum((a.quantity * a.price_unit) - (a.quantity * a.price_unit) * a.discount / 100) from account_invoice c, account_invoice_line a, budget_info_inv b "
                       " where c.id=a.invoice_id and a.invoice_id = %s and a.account_analytic_id=b.account_analytic_id and b.account_analytic_id = %s and c.id = b.invoice_id and to_char(c.date_invoice,'yyyy') = %s and c.state = 'draft' ",(invoice_id,str(account_analytic_id),str(date_end),))
            
            amount1 = cr.fetchone()
            amount1 = amount1[0] or 0.00
            
#            cr.execute(" select sum(e.subtotal) from purchase_order a, purchase_requisition b, stock_picking c, material_requisition d, material_requisition_line e, budget_info f "
#                       " where a.requisition_id = b.id and b.int_move_id = c.id and c.material_req_id = d.id and a.state in ('done','approved') "
#                       " and d.id = f.material_req_id  and e.account_analytic_id = f.account_analytic_id and d.id = e.requisition_id "
#                       " and e.requisition_id = %s and f.account_analytic_id = %s and to_char(d.date_end,'yyyy') = %s ",(material_req_id,str(account_analytic_id),str(date_end),))
#            amount2 = cr.fetchone()
#            amount2 = amount2[0] or 0.00    
            amount2 = 0.00
            #print "xxxxxxxxxxxx",amount,material_req_id,str(account_analytic_id),str(date_end)
            res[line['id']] = amount1 - amount2
        return res
    
    def _amount_utilized(self, cr, uid, ids, name, args, context=None):
        res={}
        for line in self.browse(cr, uid, ids, context=None):
            account_analytic_id = line.account_analytic_id.id
            invoice_id = line.invoice_id.id
            date_end = line.invoice_id.date_invoice and line.invoice_id.date_invoice[:4] or False
            if not date_end:
                return res
            #acc_ids = line.budget_item_id.
            
            cr.execute("SELECT SUM(amount) as balance_real FROM account_analytic_line "
                   "WHERE account_id=%s AND to_char(date,'yyyy') = %s ", (str(account_analytic_id),str(date_end),))
            amount_real = cr.fetchone()
            amount_real = amount_real[0] or 0.00
            
            #===================================================================
            # cr.execute("SELECT SUM(x.product_qty*x.price_unit) as balance_virtual FROM purchase_order_line x, purchase_order y "
            #        " WHERE x.state in ('approved','confirmed','done') and x.order_id = y.id and "
            #        " x.order_id in (select a.id from purchase_order a, account_invoice b, purchase_invoice_rel c "
            #            " where a.id=c.purchase_id and b.id= c.invoice_id and (a.state in ('confirmed','approved','done') and b.state not in ('open','paid','cancel')) and a.id=y.id) and "
            #           " x.account_analytic_id = %s and to_char(x.date_planned,'yyyy') = %s ",(str(account_analytic_id),str(date_end),))
            # amount_spent = cr.fetchone()
            # amount_spent = amount_spent[0] or 0.00
            #===================================================================
            cr.execute("select SUM(x.product_qty*x.price_unit) as balance_virtual FROM purchase_order_line x, purchase_order y "
                        " where y.state in ('approved') and x.order_id = y.id "
                        "  and x.account_analytic_id = %s and to_char(x.date_planned,'yyyy') = %s ", (str(account_analytic_id),str(date_end),))
            amount_virtual1 = cr.fetchone()
            amount_virtual1 = amount_virtual1[0] or 0.00
            
            cr.execute("SELECT SUM(a.product_qty*a.price_unit) as balance_virtual FROM purchase_order_line x, purchase_order y, stock_move a "
                     " WHERE x.order_id = y.id and a.purchase_line_id = x.id and a.state in ('cancel','done') and "
                     " x.order_id in (select a.id from purchase_order a, account_invoice b, purchase_invoice_rel c "
                       "  where a.id=c.purchase_id and b.id= c.invoice_id and (a.state in ('approved') and b.state in ('open','paid','cancel')) and a.id=y.id) and "
                       " x.account_analytic_id = %s and to_char(x.date_planned,'yyyy') = %s ",(str(account_analytic_id),str(date_end),))
            amount_virtual2 = cr.fetchone()
            amount_virtual2 = amount_virtual2[0] or 0.00
            amount_spent = amount_virtual1 - amount_virtual2
            #res[line['id']] = amount_spent
            #===================================================================
            cr.execute("select sum((a.quantity * a.price_unit) - (a.quantity * a.price_unit) * a.discount / 100) from account_invoice c, account_invoice_line a, budget_info_inv b "
                       " where c.id=a.invoice_id and a.invoice_id = %s and a.account_analytic_id=b.account_analytic_id and b.account_analytic_id = %s and c.id = b.invoice_id and to_char(c.date_invoice,'yyyy') = %s and c.state = 'draft' ",(invoice_id,str(account_analytic_id),str(date_end),))
            
            amount1 = cr.fetchone()
            amount1 = amount1[0] or 0.00
            
#            cr.execute(" select sum(e.subtotal) from purchase_order a, purchase_requisition b, stock_picking c, material_requisition d, material_requisition_line e, budget_info f "
#                       " where a.requisition_id = b.id and b.int_move_id = c.id and c.material_req_id = d.id and a.state in ('done','approved') "
#                       " and d.id = f.material_req_id  and e.account_analytic_id = f.account_analytic_id and d.id = e.requisition_id "
#                       " and e.requisition_id = %s and f.account_analytic_id = %s and to_char(d.date_end,'yyyy') = %s ",(material_req_id,str(account_analytic_id),str(date_end),))
#            amount2 = cr.fetchone()
#            amount2 = amount2[0] or 0.00    
            amount2 = 0.00
            amount_current = amount1 - amount2
            #===================================================================
            
            res[line['id']] = amount_spent + amount_current + abs(amount_real)
        return res
    
    def _amount_remain(self, cr, uid, ids, name, args, context=None):
        res={}
        for line in self.browse(cr, uid, ids, context=None):
            account_analytic_id = line.account_analytic_id.id
            invoice_id = line.invoice_id.id
            date_end = line.invoice_id.date_invoice and line.invoice_id.date_invoice[:4] or False
            if not date_end:
                return res
            #acc_ids = line.budget_item_id.
            
            cr.execute("SELECT SUM(amount) as balance_real FROM account_analytic_line "
                   "WHERE account_id=%s AND to_char(date,'yyyy') = %s ", (str(account_analytic_id),str(date_end),))
            amount_real = cr.fetchone()
            amount_real = amount_real[0] or 0.00
            
            cr.execute("select sum(a.amount) as amount_budget from ad_budget_line a, account_period b "
                       " where a.analytic_account_id = %s and a.period_id = b.id and to_char(b.date_start,'yyyy') = %s ",(str(account_analytic_id),str(date_end),))
            amount_budget = cr.fetchone()
            amount_budget = amount_budget[0] or 0.00
            
            #===================================================================
            # cr.execute("SELECT SUM(x.product_qty*x.price_unit) as balance_virtual FROM purchase_order_line x, purchase_order y "
            #        " WHERE x.state in ('approved','confirmed','done') and x.order_id = y.id and "
            #        " x.order_id in (select a.id from purchase_order a, account_invoice b, purchase_invoice_rel c "
            #            " where a.id=c.purchase_id and b.id= c.invoice_id and (a.state in ('confirmed','approved','done') and b.state not in ('open','paid','cancel')) and a.id=y.id) and "
            #           " x.account_analytic_id = %s and to_char(x.date_planned,'yyyy') = %s ",(str(account_analytic_id),str(date_end),))
            # amount_spent = cr.fetchone()
            # amount_spent = amount_spent[0] or 0.00
            #===================================================================
            cr.execute("select SUM(x.product_qty*x.price_unit) as balance_virtual FROM purchase_order_line x, purchase_order y "
                        " where y.state in ('approved') and x.order_id = y.id "
                        "  and x.account_analytic_id = %s and to_char(x.date_planned,'yyyy') = %s ", (str(account_analytic_id),str(date_end),))
            amount_virtual1 = cr.fetchone()
            amount_virtual1 = amount_virtual1[0] or 0.00
            
            cr.execute("SELECT SUM(a.product_qty*a.price_unit) as balance_virtual FROM purchase_order_line x, purchase_order y, stock_move a "
                     " WHERE x.order_id = y.id and a.purchase_line_id = x.id and a.state in ('cancel','done') and "
                     " x.order_id in (select a.id from purchase_order a, account_invoice b, purchase_invoice_rel c "
                       "  where a.id=c.purchase_id and b.id= c.invoice_id and (a.state in ('approved') and b.state in ('open','paid','cancel')) and a.id=y.id) and "
                       " x.account_analytic_id = %s and to_char(x.date_planned,'yyyy') = %s ",(str(account_analytic_id),str(date_end),))
            amount_virtual2 = cr.fetchone()
            amount_virtual2 = amount_virtual2[0] or 0.00
            amount_spent = amount_virtual1 - amount_virtual2
            #res[line['id']] = amount_spent
            #===================================================================
            cr.execute("select sum((a.quantity * a.price_unit) - (a.quantity * a.price_unit) * a.discount / 100) from account_invoice c, account_invoice_line a, budget_info_inv b "
                       " where c.id=a.invoice_id and a.invoice_id = %s and a.account_analytic_id=b.account_analytic_id and b.account_analytic_id = %s and c.id = b.invoice_id and to_char(c.date_invoice,'yyyy') = %s and c.state = 'draft'",(invoice_id,str(account_analytic_id),str(date_end),))
            
            amount1 = cr.fetchone()
            amount1 = amount1[0] or 0.00
            
#            cr.execute(" select sum(e.subtotal) from purchase_order a, purchase_requisition b, stock_picking c, material_requisition d, material_requisition_line e, budget_info f "
#                       " where a.requisition_id = b.id and b.int_move_id = c.id and c.material_req_id = d.id and a.state in ('done','approved') "
#                       " and d.id = f.material_req_id  and e.account_analytic_id = f.account_analytic_id and d.id = e.requisition_id "
#                       " and e.requisition_id = %s and f.account_analytic_id = %s and to_char(d.date_end,'yyyy') = %s ",(material_req_id,str(account_analytic_id),str(date_end),))
#            amount2 = cr.fetchone()
#            amount2 = amount2[0] or 0.00    
            amount2 = 0.00
            amount_current = amount1 - amount2
            #print amount1,amount2,amount_current,amount_budget - (amount_spent + amount_current + abs(amount_real))
            #===================================================================
            res[line['id']] = amount_budget - (amount_spent + amount_current + abs(amount_real))
        return res
    
    _columns = {
        'name': fields.char('Name', 64),
        'account_analytic_id':fields.many2one('account.analytic.account', 'Analytic Account',),
        #'material_req_id': fields.many2one('material.requisition', 'Material Request'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice'),
        #'budget_line_id': fields.many2one('ad_budget.line', 'Budget Lines'),
        'amount_budget': fields.function(_amount_budget, digits=(20,0), method=True, string='Budget Amount', type='float'),
        'amount_spent': fields.function(_amount_spent, digits=(20,0), method=True, string='Budget Spent', type='float'),
        'amount_current': fields.function(_amount_current, digits=(20,0), method=True, string='Budget Current', type='float'),
        'amount_utilized': fields.function(_amount_utilized, digits=(20,0), method=True, string='Budget Utilized', type='float'),
        'amount_remain': fields.function(_amount_remain, digits=(20,0), method=True, string='Budget Remain', type='float'),
    }
budget_info_inv()


class account_invoice_tax(osv.osv):
    _inherit = 'account.invoice.tax'
    
    _columns = {
            'account_analytic_id'   :fields.many2one('account.analytic.account', 'Analytic Account',),
                }
    
    def compute(self, cr, uid, invoice_id, context=None):
        print "xxxxx444"
        
        if context is None:
            context = {}
        tax_grouped = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context)
        cur = inv.currency_id
        company_currency = inv.company_id.currency_id.id
        
        ###################Budget Info#####################
        print "222222222222222222222", inv.id
        #self.pool.get('account.invoice').compute_budget_info(cr, uid, inv.id, context=None)
        ###################################################
        
        for line in inv.invoice_line:
            ## INHERIT -- START
            invline_taxes = self._global_amount_compute(cr, uid, inv, line.invoice_line_tax_id, context=context)
            ## INHERIT -- END

            #for tax in tax_obj.compute(cr, uid, invline_taxes, (line.price_unit* (1-(line.discount or 0.0)/100.0)-30000), line.quantity, inv.address_invoice_id.id, line.product_id, inv.partner_id):
            ####################Retention##########################   
            
            #for tax in tax_obj.compute(cr, uid, invline_taxes, (line.price_unit* (1-(line.discount or 0.0)/100.0)-inv.amount_dp-line.retention), line.quantity, inv.address_invoice_id.id, line.product_id, inv.partner_id):
            if inv.retention_check == True:
                dpp = (line.price_unit* (1-(line.discount or 0.0)/100.0))
                print "line.price_unit", line.price_unit
                print "inv.amount_dp", inv.amount_dp
                print "line.retention", line.retention
                print "DPP ::::::", dpp
            else:
                dpp = (line.price_unit* (1-(line.discount or 0.0)/100.0))
            print "invline_taxes++++++++++++++++++++++++++", invline_taxes, dpp
            for tax in tax_obj.compute(cr, uid, invline_taxes, dpp, line.quantity, inv.address_invoice_id.id, line.product_id, inv.partner_id):
            #######################################################
                print "-------------------------------------VAL", tax
                val={}
                val['invoice_id'] = inv.id
                val['name'] = tax['name']
                val['amount'] = tax['amount']
                val['manual'] = False
                val['sequence'] = tax['sequence']
                val['base'] = tax['price_unit'] * line['quantity'] 
                
                print "**********************************val['amount']", val['amount']
                
                if val['amount'] < 0 and inv.retention_check == True:
                    #print "line.retention%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%", line.retention
                    advance_tax_base = inv.amount_dp / 1.1
                    dpp_wth = dpp - line.retention - advance_tax_base
                    
                    print "dpp",            dpp
                    print "line.retention", line.retention
                    print "advance_tax_base", advance_tax_base
                    print "invline_taxes", invline_taxes
                    
                    invline_taxes_wth = tax_obj.browse(cr, uid, tax['id'])
                    print "invline_taxes_wth###########################################################", invline_taxes_wth
                    
                    for tax_wth in tax_obj.compute(cr, uid, [invline_taxes_wth], dpp_wth, line.quantity, inv.address_invoice_id.id, line.product_id, inv.partner_id):
                        #print "val['base']", val['base']
                        val['base']     = tax_wth['price_unit'] * line['quantity']
                        val['amount']   = tax_wth['amount']
                        
                elif val['amount'] > 0 and inv.retention_check == True:
                    
                    invline_taxes_vat = tax_obj.browse(cr, uid, tax['id'])
                    print "invline_taxes_wth@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@", invline_taxes_vat
                    dpp_vat = dpp - line.retention
                    for tax_vat in tax_obj.compute(cr, uid, [invline_taxes_vat], dpp_vat, line.quantity, inv.address_invoice_id.id, line.product_id, inv.partner_id):
                        #print "val['base']", val['base']
                        val['base']     = tax_vat['price_unit'] * line['quantity']
                        val['amount']   = tax_vat['amount']
##                
                
                else:
                    val['base'] = tax['price_unit'] * line['quantity'] 

                if inv.type in ('out_invoice','in_invoice'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
                    if val['tax_amount'] > 0.0:
                        val['account_analytic_id'] = line.account_analytic_id.id
                    else:
                        val['account_analytic_id'] = False
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['account_id'] = tax['account_paid_id'] or line.account_id.id

                key = (val['tax_code_id'], val['base_code_id'], val['account_id'])
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']

        for t in tax_grouped.values():
            t['base'] = cur_obj.round(cr, uid, cur, t['base'])
            t['amount'] = cur_obj.round(cr, uid, cur, t['amount'])
            t['base_amount'] = cur_obj.round(cr, uid, cur, t['base_amount'])
            t['tax_amount'] = cur_obj.round(cr, uid, cur, t['tax_amount'])
        return tax_grouped

account_invoice_tax()

class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'
    
    _columns = {
            'retention'         : fields.float('Retention'),
                }
    
account_invoice_line()

class account_invoice(osv.osv):
    
    _inherit = 'account.invoice'
    
    ##################Budget Info######################
    def compute_budget_info(self, cr, uid, ids, context=None):
        print "IDS________________________", cr, uid, ids
        print "BISA", self.pool.get('account.invoice').browse(cr, uid, ids)
        
        for mr in self.browse(cr, uid, ids):
            print "AAAAAAAAAAAAAAAAAAAA"
            if ids:
                mat = int(str(ids[0]))
                print "BBBBBBBBBBBBBBBBB", mat
                cr.execute('delete from budget_info_inv where invoice_id = %s ',(mat,))
            for lines in self.browse(cr, uid, ids)[0].invoice_line:
                invoice_id = ids[0]
                #subtotal = lines.product_qty * lines.price
                subtotal = lines.discount/100 * (lines.quantity * lines.price_unit)
                account_analytic_id = lines.account_analytic_id.id
                print "subtotal :::", lines.account_analytic_id.id,ids[0]
                #subtotal.update(subtotal)
                vals = {
                    'subtotal' : subtotal
                }
                #self.pool.get('cash.advance.line').write(cr, uid, [lines.id], vals, context=context)
                budget_obj =  self.pool.get('budget.info.inv')
                if account_analytic_id and invoice_id:
                    info = budget_obj.search(cr, uid, [('account_analytic_id','=', account_analytic_id),('invoice_id','=',invoice_id)])
                    if not info:
                        budgets = {
                            'name': '/',
                            'account_analytic_id': account_analytic_id,
                            'invoice_id': invoice_id,
                        }
                        print "budgets", budgets
                        budget_id = budget_obj.create(cr, uid, budgets)
                        cr.execute('INSERT INTO budget_info_rel_inv (invoice_id, budget_info_id) values (%s,%s)',(invoice_id,budget_id))
                        #cr.execute('INSERT INTO budget_info_rel (material_req_id, budget_info_id) values (%s,%s)',(material_req_id,budget_id))
            return True
    ##################################################
    ###################RETENTION#########################
    def _amount_all(self, cr, uid, ids, name, args, context=None):
        print "hOOOOOOOOOOOOOOOOOOOOOOLLLLLLLLLLLLLLLLLLLLLAAAAAAAAAAAAA"
        print "_amount_all"
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'amount_ppn': 0.0,
                'holding_taxes': 0.0,
                'sub_total': 0.0,
                
            }
            
            #if data['form']['direction_selection'] == 'past':
            
            for line in invoice.tax_line:
                if line['base_code_id']['ppn'] == True:
                    print "TRUE"
                    res[invoice.id]['amount_ppn'] += line.amount
            
                
            for line in invoice.tax_line:
                if line['base_code_id']['ppn'] == False:
                    print "TRUE"
                    res[invoice.id]['holding_taxes'] += abs(line.amount)
            
            
            
            for line in invoice.invoice_line:
                res[invoice.id]['amount_untaxed'] += line.price_subtotal
                print "line.price_subtotal", line.price_subtotal
                
            for line in invoice.tax_line:
                res[invoice.id]['amount_tax'] += line.amount
                print "line.amount", line.amount
            ###################RETENTION#########################
            retention_amount = 0.0
            for ret in invoice.invoice_line:
                retention_amount += ret.retention
            print "retention_amount", retention_amount
            #retention = invoice.invoice_line[0].retention
            if invoice.retention_check == True:
                res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed'] - retention_amount
            else:
                res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed']
            ####################################################
            res[invoice.id]['sub_total'] = res[invoice.id]['amount_ppn'] + res[invoice.id]['amount_untaxed']

        return res
        #########################################################
    
    def _amount_residual(self, cr, uid, ids, name, args, context=None):
        print "123wwww"
        result = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            print "inv-----", invoice
            result[invoice.id] = 0.0
            if invoice.move_id:
                for m in invoice.move_id.line_id:
                    if m.account_id.type in ('receivable','payable'):
                        result[invoice.id] += m.amount_residual_currency
        print "result[invoice.id]---->>", result[invoice.id]
        print "result---------------->>", result
        return result
    
#    def _dp_residual(self, cr, uid, ids, name, args, context=None):
#        result = {}
#        for invoice in self.browse(cr, uid, ids, context=context):
#            result[invoice.id] = 0.0
#            if invoice.downpayment_id:
#                for line in invoice.downpayment_id.dp_line:
#                    if line.state == 'paid':
#                        result[invoice.id] += line.amount
#                result[invoice.id] = result[invoice.id] - invoice.downpayment_id.downpayment_used
#        print "result[invoice.id]--==----===", result[invoice.id]
#        print "Result :::", result
#        return result
    
    def _dp_residual(self, cr, uid, ids, name, args, context=None):
        result = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            result[invoice.id] = 0.0
            if invoice.downpayment_id:
                for line in invoice.downpayment_id.dp_line:
                    if line.state == 'paid':
                        result[invoice.id] += line.amount
                #result[invoice.id] = result[invoice.id] - invoice.downpayment_id.downpayment_used
        
        ####################   
        #v_s = self.pool.get('account.voucher.line').search(cr, uid, [('downpayment_id', '=', invoice.downpayment_id.id),('voucher_id.state','=','posted')])
        #v_b = self.pool.get('account.voucher.line').browse(cr, uid, v_s)
        
        v_s = self.pool.get('account.invoice').search(cr, uid, [('downpayment_id', '=', invoice.downpayment_id.id),('state','not in',['draft','cancel'])])
        v_b = self.pool.get('account.invoice').browse(cr, uid, v_s)
        
        total_used = 0.0
        for x in v_b:
            total_used += x.amount_dp
            #total_used += x.amount_dp_original
        result[invoice.id] = result[invoice.id] - total_used
        #print "result[invoice.id]--==----===", result[invoice.id]
        #print "Result :::", result
        return result
    
    _columns = {
            ################Budget Info###################
            #'budget_info_ids_inv': fields.many2many('budget.info.inv', 'budget_info_rel_inv', 'invoice_id', 'budget_info_id', 'Budget Line', readonly=True),
            'budget_info_ids_inv' : fields.one2many('budget.info.inv', 'invoice_id', 'Budget Lines'),
            ##############################################
            'account_voc_line'  : fields.one2many('account.voucher', 'invoice_id' ,"Account Voc", readonly=True),
            ##################################################
            'downpayment_id'    : fields.many2one('downpayment','Downpayment'),
            'amount_dp'         : fields.float('Amount Downpayment'),
            'downpayment_id'    : fields.many2one('downpayment', 'Downpayment'),
            'dp_residual'       : fields.function(_dp_residual, method=True, string='DP Residual', digits_compute=dp.get_precision('Account'), help="Remaining amount due."),
            'retention_check'   : fields.boolean('With Retention'),
            ##################################################
                }
    def onchange_retention_check(self, cr, uid, ids, context=None):
        for invoice in self.browse(cr, uid, ids, context=context):
            retention_account_id = invoice.company_id.retention_account_id.id
        if not retention_account_id:
            warning = {
                    "title": ("No Retention Account !"),
                    "message": ("You must define a retention account !")
                }
            return {'warning': warning, 'value': {'retention_check': False}}
        
    
    def on_change_check_dp(self, cr, uid, ids, amount_dp, context=None):
        #amount_dp = False
        if ids:
            dp_residual = 0.0
            for invoice in self.browse(cr, uid, ids, context=context):
                currency = invoice.currency_id.name
                if invoice.downpayment_id:
                    for line in invoice.downpayment_id.dp_line:
                        amount_dp_line = line.amount
                        dp_residual     += amount_dp_line
                    #dp_residual = dp_residual - invoice.downpayment_id.downpayment_used
                    
                    
            #v_s = self.pool.get('account.voucher.line').search(cr, uid, [('downpayment_id', '=', invoice.downpayment_id.id),('voucher_id.state','=','posted')])
            #v_b = self.pool.get('account.voucher.line').browse(cr, uid, v_s)
            
            v_s = self.search(cr, uid, [('downpayment_id','=',invoice.downpayment_id.id),('state','not in',['draft','cancel'])])
            v_b = self.browse(cr, uid, v_s)
            
            
            total_used = 0.0
            for x in v_b:
                total_used += x.amount_dp
                #total_used += x.amount_dp_original
            dp_residual = dp_residual - total_used
                
            if amount_dp > dp_residual:
                warning = {
                    "title": ("Bad Downpayment Amount !"),
                    "message": (("Your Downpayment Amount Can not more than (%s) %s")%(currency,dp_residual))
                }
                return {'warning': warning, 'value': {'amount_dp': 0.0}}
            else:
                return {'value': {'amount_dp': amount_dp}}
        return {'value': {'amount_dp': amount_dp}}
    
#    def on_change_check_dp(self, cr, uid, ids, amount_dp, context=None):
#        dp_residual = 0.0
#        for invoice in self.browse(cr, uid, ids, context=context):
#            if invoice.downpayment_id:
#                for line in invoice.downpayment_id.dp_line:
#                    amount_dp_line = line.amount
#                    dp_residual     += amount_dp_line
#                dp_residual = dp_residual - invoice.downpayment_id.downpayment_used
#            
#                if amount_dp > dp_residual:
#                    warning = {
#                        "title": ("Bad Downpayment Amount !"),
#                        "message": ("Your Downpayment Amount Can not more than '")
#                    }
#                    return {'warning': warning, 'value': {'amount_dp': 0.0}}
#                else:
#                    return {'value': {'amount_dp': amount_dp}}
#        return {'value': {'amount_dp': amount_dp}}
    
    _defaults = {
            'amount_dp' : 0.0,
                 }
    
account_invoice()