from osv import osv, fields
from tools.translate import _
import time
import datetime

class res_currency_tax_rate(osv.osv):
    _name = "res.currency.tax.rate"
    _description = "Currency Tax Rate"

    _columns = {
        'name': fields.date('From Date', required=True, select=True),
        'date_until': fields.date('To Date ', required=True, select=True),
        'rate': fields.float('Rate', digits=(12,6), help='The rate of the currency to the currency of rate 1'),
        'currency_id': fields.many2one('res.currency', 'Currency', readonly=True),
        'currency_rate_type_id': fields.many2one('res.currency.rate.type', 'Currency Rate Type', help="Allow you to define your own currency rate types, like 'Average' or 'Year to Date'. Leave empty if you simply want to use the normal 'spot' rate type"),
        'kp_men': fields.char('Kep. Menteri Keuangan No.'),
        'date_release': fields.date('Tgl Keputusan'),
    }
    _defaults = {
        'name': lambda *a: time.strftime('%Y-%m-%d'),
    }
    _order = "name desc"
res_currency_tax_rate()

class res_currency(osv.osv):
    _inherit = 'res.currency'
    _description = 'res currency'
    
    def computerate(self, cr, uid, from_currency_id, to_currency_id, from_amount, round=True, currency_rate_type_from=False, currency_rate_type_to=False, context=None):
        if not context:
            context = {}
        if not from_currency_id:
            from_currency_id = to_currency_id
        if not to_currency_id:
            to_currency_id = from_currency_id
        xc = self.browse(cr, uid, [from_currency_id,to_currency_id], context=context)
        from_currency = (xc[0].id == from_currency_id and xc[0]) or xc[1]
        to_currency = (xc[0].id == to_currency_id and xc[0]) or xc[1]
        trans_currency_id = context.get('trans_currency',False)
        #first check whether the tax currency if same with company currency
        #from currency_id : tax currency
        if (to_currency_id == from_currency_id) and (currency_rate_type_from == currency_rate_type_to):
            #check if transaction is using rounding
            if round:
                return self.round(cr, uid, to_currency, from_amount)
            else:
                return from_amount
        else:
            context.update({'currency_rate_type_from': currency_rate_type_from, 'currency_rate_type_to': currency_rate_type_to})
            # print "xc======================",xc[0].name
            warning_currency=xc[0] and xc[0].name or ''
            if context.get('reverse',False):
                warning_currency = xc[1].name
                tax_rate_ids = self.pool.get('res.currency.tax.rate').search(cr, uid, [('currency_id','=',to_currency_id),('name','<=',context.get('date',datetime.date.today().strftime('%Y-%m-%d')))], context=context)    
                # print "=============1=============",from_currency,to_currency,tax_rate_ids,context
            else:
                tax_rate_ids = self.pool.get('res.currency.tax.rate').search(cr, uid, [('currency_id','=',from_currency_id),('name','<=',context.get('date',datetime.date.today().strftime('%Y-%m-%d')))], context=context)
                # print "=============2=============",from_currency,to_currency,tax_rate_ids,context
            
            if tax_rate_ids:
                tax_rate = self.pool.get('res.currency.tax.rate').browse(cr,uid,tax_rate_ids)[0]
                if tax_rate.rate > 1.0 and not context.get('reverse',False):
                    from_amount = from_amount * tax_rate.rate
                else:
                    # print "xxxxxxxxxxxxxxxxxxxxxx", from_amount,tax_rate.rate
                    from_amount = from_amount / tax_rate.rate
                # print "tax_rate================",from_amount,tax_rate.rate
                if round:
                    return self.round(cr, uid, to_currency, from_amount)
                else:
                    return from_amount
            else:
                raise osv.except_osv(_('Warning!'), _('Please Insert Rate Pajak for %s currency') %(warning_currency) )

    # def computerate(self, cr, uid, from_currency_id, to_currency_id, from_amount, round=True, currency_rate_type_from=False, currency_rate_type_to=False, context=None):
    #     if not context:
    #         context = {}
    #     if not from_currency_id:
    #         from_currency_id = to_currency_id
    #     if not to_currency_id:
    #         to_currency_id = from_currency_id
    #     xc = self.browse(cr, uid, [from_currency_id,to_currency_id], context=context)
    #     from_currency = (xc[0].id == from_currency_id and xc[0]) or xc[1]
    #     to_currency = (xc[0].id == to_currency_id and xc[0]) or xc[1]
    #     trans_currency = context.get('trans_currency',False)

    #     if (to_currency_id == from_currency_id) and (currency_rate_type_from == currency_rate_type_to):
    #         if trans_currency != from_currency:
    #             tax_rate_ids = self.pool.get('res.currency.tax.rate').search(cr, uid, [('currency_id','=',from_currency_id),('name','<=',context.get('date',datetime.date.today().strftime('%Y-%m-%d')))], context=context)
                
    #             if tax_rate_ids:
    #                 tax_rate = self.pool.get('res.currency.tax.rate').browse(cr,uid,tax_rate_ids)[0]
    #                 from_amount = from_amount / tax_rate
    #             else:
    #                 raise osv.except_osv(_('Warning!'), _('Please Insert Rate Pajak for %s currency')%(xc[0].name))

    #             if round:
    #                 return self.round(cr, uid, to_currency, from_amount)
    #             else:
    #                 return from_amount
    #         else:
    #             if round:
    #                 return self.round(cr, uid, to_currency, from_amount)
    #             else:
    #                 return from_amount
    #     else:
    #         context.update({'currency_rate_type_from': currency_rate_type_from, 'currency_rate_type_to': currency_rate_type_to})
    #         from_currency = self.pool.get('res.currency.tax.rate').search(cr, uid, [('currency_id','=',from_currency_id)], context=context)
    #         from_currency1 = self.pool.get('res.currency.tax.rate').browse(cr, uid, from_currency, context=context)
    #         rate = {}
    #         i = 0;
            
    #         for f in from_currency1:

    #             if context['date'] == f.name:

    #                 rate[i] = f.rate
    #                 i+=1

    #             else:
    #                 if context['date'] > f.name:

    #                     rate[i] = f.rate
    #                     i+=1
    
    #         if rate.has_key(0):          
    #             if round:
    #                 return self.round(cr, uid, to_currency, from_amount / rate[0])
    #             else:
    #                 return from_amount / rate[0]
    #         else:
    #             raise osv.except_osv(_('Warning!'), _('Please Insert Rate Pajak'))
                
    
    _columns = {
        'rate_tax_ids': fields.one2many('res.currency.tax.rate', 'currency_id', string='Res Currency'),
    }

res_currency()
