from osv import fields, osv
from report import report_sxw
import pooler
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby
from report_webkit import webkit_report
from tools.translate import _
import netsvc
import tools
import decimal_precision as dp
import logging
from dateutil import tz
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP

class ReportSalesSummary(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(ReportSalesSummary, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_object' : self._get_object,
            'get_goods_type': self._get_goods_type,
            'get_date_from': self._get_date_from,
            'get_date_to': self._get_date_to,
            'get_data_so': self._get_data_so,
            'get_product_qty': self._get_product_qty,
            'get_product_sale_price': self._get_product_sale_price,
            'get_product_cost_price': self._get_product_cost_price,
            'get_product_net_price': self._get_product_net_price,
            'get_so_line': self._get_so_line,
            'get_move_ids': self._get_move_ids,
            'get_view': self._get_view,
            'xdate': self._xdate,
            'get_title': self._get_title,            
            'uom_to_bales': self._uom_to_bales,            
            'uom_to_kgs': self._uom_to_kgs,            
            'uom_to_base': self._uom_to_base,            
            'price_per_bales': self._price_per_bales,
            'price_per_kgs': self._price_per_kgs,
            'price_per_base': self._price_per_base,            
            'get_company': self._get_company, 
            'get_uom_base': self._get_uom_base,           
            'get_price_base': self._get_price_base, 
            'get_print_user_time': self._get_print_user_time,     
            'get_base_currency': self._get_base_currency,  
            'get_opt_currency' : self._get_opt_currency,   
        })
    def _get_print_user_time(self,context=None):
        cr = self.cr
        uid = self.uid
        curr_user = self.pool.get('res.users').browse(cr, uid, [uid], context=context)[0]
        localtz = tz.tzlocal()
        print_user_time = 'Printed By ' + curr_user.partner_id.name + ' On ' + datetime.now(localtz).strftime('%d/%m/%Y %H:%M')
        return print_user_time

    def _xdate(self,x):
        try:
            x1 = x[:10]
        except:
            x1 = ''

        try:
            y = datetime.strptime(x1,'%Y-%m-%d').strftime('%d/%m/%Y')
        except:
            y = x1
        return y

    def _get_title(self,data,sheet):
        if data['form']['sale_type'] == 'export':
            stitle = 'EXPORT '
        elif data['form']['sale_type'] == 'local':
            stitle = 'LOCAL '
        else:
            stitle = ''
        usage = data['form']['sale_type'] == 'internal' and 'RETURN ' or ''
        stitle = stitle + 'SALES '+usage+'SUMMARY STATEMENT - '
        if sheet == 'customer':
            stitle = stitle + 'CUSTOMER WISE'
        elif sheet == 'product':
            stitle = stitle + 'PRODUCT WISE'
        elif sheet == 'date':
            stitle = stitle + 'DATE WISE'
        elif sheet == 'country':
            stitle = stitle + 'COUNTRY WISE'
        if data['form']['sale_type'] == 'local':
            if data['form']['locale_sale_type'] == 'okb':
                stitle = stitle + ' - OUTSIDE KAWASAN BERIKAT'
            elif data['form']['locale_sale_type'] == 'ikb':
                stitle = stitle + ' - INSIDE KAWASAN BERIKAT'
        return stitle

    def _get_uom_base(self,data):
        if data['form']['goods_type'] == 'finish_others' or data['form']['goods_type'] == 'waste' or data['form']['goods_type'] == 'asset':
          uom_base = 'KGS'
        elif data['form']['sale_type'] == 'export' or data['form']['sale_type'] == 'local':
          uom_base = 'BALES'
        else:
          uom_base = 'KGS'
        return uom_base

    def _get_price_base(self,data):
        self.cr.execute ("select coalesce(b.name,'') \
                          from res_company a \
                          left join res_currency b on a.currency_id = b.id")

        res = self.cr.fetchone()

        currency_name = res[0] or ''

        if data['form']['goods_type'] == 'finish_others' or data['form']['goods_type'] == 'waste' or data['form']['goods_type'] == 'asset':
          price_base = currency_name + '/KG'
        elif data['form']['sale_type'] == 'export' or data['form']['sale_type'] == 'local':
          price_base = currency_name + '/BALE'
        else:
          price_base = currency_name + '/KG'
        return price_base

    def _get_opt_currency(self,data):
        self.cr.execute ("select name \
                          from res_currency \
                          where id = %s", 
                        (data['form']['currency_id'][0],))

        res = self.cr.fetchone()

        currency_name = res[0] or ''
        return currency_name

    def _uom_to_bales(self,qty,uom_source):
        cr = self.cr
        uid = self.uid
        bale = self.pool.get('product.uom').search(cr,uid,[('name','=','BALES')])
        qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, qty, to_uom_id=bale and bale[0] or False)
        return qty_result

    def _uom_to_kgs(self,qty,uom_source):
        cr = self.cr
        uid = self.uid
        bale = self.pool.get('product.uom').search(cr,uid,[('name','=','KGS')])
        qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, qty, to_uom_id=bale and bale[0] or False)
        return qty_result

    def _uom_to_base(self,data,qty,uom_source):
        cr = self.cr
        uid = self.uid
        if data['form']['goods_type'] == 'finish_others' or data['form']['goods_type'] == 'waste' or data['form']['goods_type'] == 'asset':
          uom_base = 'KGS'
        elif data['form']['sale_type'] == 'export' or data['form']['sale_type'] == 'local':
          uom_base = 'BALES'
        else:
          uom_base = 'KGS'
        base = self.pool.get('product.uom').search(cr,uid,[('name','=',uom_base)])
        qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, qty, to_uom_id=base and base[0] or False)
        return qty_result

    def _price_per_bales(self,price,uom_source):
        cr = self.cr
        uid = self.uid
        bale = self.pool.get('product.uom').search(cr,uid,[('name','=','BALES')])
        qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, 1000.0, to_uom_id=bale and bale[0] or False)
        if qty_result>0:
          price_result = price*1000.0/qty_result 
        else:
          price_result = price 
        return price_result

    def _price_per_kgs(self,price,uom_source):
        cr = self.cr
        uid = self.uid
        bale = self.pool.get('product.uom').search(cr,uid,[('name','=','KGS')])
        qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, 1000.0, to_uom_id=bale and bale[0] or False)
        if qty_result>0:
          price_result = price*1000.0/qty_result 
        else:
          price_result = price 
        return price_result

    def _price_per_base(self,data,price,uom_source):
        cr = self.cr
        uid = self.uid
        if data['form']['goods_type'] == 'finish_others' or data['form']['goods_type'] == 'waste' or data['form']['goods_type'] == 'asset':
          uom_base = 'KGS'
        elif data['form']['sale_type'] == 'export' or data['form']['sale_type'] == 'local':
          uom_base = 'BALES'
        else:
          uom_base = 'KGS'
        base = self.pool.get('product.uom').search(cr,uid,[('name','=',uom_base)])
        qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, 1000.0, to_uom_id=base and base[0] or False)
        if qty_result>0:
          price_result = price*1000.0/qty_result 
        else:
          price_result = price 
        return price_result
        
    def _get_object(self,data):
        obj_data=self.pool.get(data['model']).browse(self.cr,self.uid,[data['form']['id']])
        return obj_data
    
    def _get_goods_type(self,data,context=None):
        if data['form']['goods_type'] == 'finish':
            return 'FINISH GOODS'
        elif data['form']['goods_type'] == 'finish_other':
            return 'FINISH GOODS'
        elif data['form']['goods_type'] == 'raw':
            return 'RAW MATERIAL'
        elif data['form']['goods_type'] == 'service':
            return 'SERVICES'
        elif data['form']['goods_type'] == 'waste':
            return 'WASTE'
        elif data['form']['goods_type'] == 'scrap':
            return 'SCRAP'
        elif data['form']['goods_type'] == 'asset':
            return 'FIXED ASSET'
        else:
            return ''
        
    def _get_date_from(self,data,context=None):
        return datetime.strptime(data['form']['date_from'],'%Y-%m-%d').strftime('%d/%m/%Y')
    
    def _get_date_to(self,data,context=None):
        return datetime.strptime(data['form']['date_to'],'%Y-%m-%d').strftime('%d/%m/%Y')
    
    def _get_data_so(self,data,context=None):
        sale_obj    = self.pool.get('sale.order')
        sale_ids    = False
        if data['form']['sale_type'] == 'export':
            sale_ids        = sale_obj.search(self.cr, self.uid, [('state','not in',('draft','cancel')),
                                                        ('goods_type','=',data['form']['goods_type']),
                                                        ('sale_type','=',data['form']['sale_type']),
                                                        ('date_order','>=',data['form']['date_from']),
                                                        ('date_order','<=',data['form']['date_to'])])
        elif data['form']['sale_type'] == 'local':
            sale_ids        = sale_obj.search(self.cr, self.uid, [('state','not in',('draft','cancel')),
                                                        ('goods_type','=',data['form']['goods_type']),
                                                        ('sale_type','=',data['form']['sale_type']),
                                                        ('locale_sale_type','=',data['form']['locale_sale_type']),
                                                        ('date_order','>=',data['form']['date_from']),
                                                        ('date_order','<=',data['form']['date_to'])])
            if sale_ids:
                sale_data = sale_obj.browse(self.cr, self.uid,sale_ids)
                return sale_data
        return {}
    
    def _get_product_qty(self,data,form,context=None):
        move_obj    = self.pool.get('stock.move')
        product_uom = self.pool.get('product.uom')
        move_data   = move_obj.browse(self.cr, self.uid,[data])[0]
        return product_uom._compute_qty(self.cr,self.uid,move_data.product_uom.id,move_data.product_uos_qty,form['form']['def_uom'][0])
    
    def _get_product_sale_price(self,data,form,context=None):
        move_obj    = self.pool.get('stock.move')
        product_uom = self.pool.get('product.uom')
        move_data   = move_obj.browse(self.cr, self.uid,[data])[0]
        return product_uom._compute_price(self.cr,self.uid,move_data.product_uom.id,move_data.sale_line_id.price_unit,form['form']['def_uom'][0])
    
    def _get_product_cost_price(self,data,form,context=None):
        move_obj    = self.pool.get('stock.move')
        product_uom = self.pool.get('product.uom')
        move_data   = move_obj.browse(self.cr, self.uid,[data])[0]
        return product_uom._compute_price(self.cr,self.uid,move_data.product_uom.id,move_data.price_unit,form['form']['def_uom'][0])
    
    def _get_product_net_price(self,data,form,context=None):
        move_obj    = self.pool.get('stock.move')
        product_uom = self.pool.get('product.uom')
        move_data   = move_obj.browse(self.cr, self.uid,[data])[0]
        return product_uom._compute_price(self.cr,self.uid,move_data.product_uom.id,move_data.price_unit,move_data.product_id.uom_id.id)
    
    def _get_so_line(self,data,context=None):
        sale_line_obj   = self.pool.get('sale.order.line')
        sale_line_ids   = sale_line_obj.search(self.cr, self.uid,[('id','=',data)])
        return sale_line_obj.browse(self.cr, self.uid,sale_line_ids)[0]
    
    def _get_move_ids(self,data,context=None):
        print data['date_from']
        print data['date_to']
        sale_obj    = self.pool.get('sale.order')
        pick_obj    = self.pool.get('stock.picking')
        move_obj    = self.pool.get('stock.move')
        sale_ids    = False
        if data['form']['sale_type'] == 'export':
            sale_ids        = sale_obj.search(self.cr, self.uid, [('state','not in',('draft','cancel')),
                                                        ('goods_type','=',data['form']['goods_type']),
                                                        ('sale_type','=',data['form']['sale_type'])])
        elif data['form']['sale_type'] == 'local':
            sale_ids        = sale_obj.search(self.cr, self.uid, [('state','not in',('draft','cancel')),
                                                        ('goods_type','=',data['form']['goods_type']),
                                                        ('sale_type','=',data['form']['sale_type']),
                                                        ('locale_sale_type','=',data['form']['locale_sale_type'])])
        if sale_ids:
            picking_ids = pick_obj.search(self.cr,self.uid,[('sale_id','in',sale_ids),('date_done','>=',data['form']['date_from']),
                                                        ('date_done','<=',data['form']['date_to']),('state','=','done')])
            if picking_ids:
                self.cr.execute("""
                    select xx.id from (select sm.id,sm.location_id,sm.product_id,pp.blend_code
                    from stock_move sm 
                    left join product_product pp on sm.product_id=pp.id 
                    where sm.picking_id in """+str(tuple(picking_ids))+""" and date >='"""+data['form']['date_from']+""" 00:00:00' and date <='"""+data['form']['date_to']+""" 23:59:59' 
                    order by sm.location_id asc, pp.blend_code asc, sm.product_id asc)xx
                    """)   
                move_ids = [x[0] for x in self.cr.fetchall()]
                
                return move_obj.browse(self.cr,self.uid,move_ids)
        return False
        
    def _get_company(self,context=None):
        self.cr.execute ("select upper(b.name) as name \
                          from res_company a \
                          left join res_partner b on a.partner_id = b.id")

        res = self.cr.fetchone()
        return res

    def _get_base_currency(self,context=None):
        self.cr.execute ("select a.currency_id,a.tax_base_currency, \
                          coalesce(b.name,'') as currency_name, \
                          coalesce(c.name,'') as tax_base_currency_name \
                          from res_company a \
                          left join res_currency b on a.currency_id = b.id \
                          left join res_currency c on a.tax_base_currency = c.id")

        res = self.cr.dictfetchall()
        return res

    def _get_view(self,data,sheet,context=None):
        s1 = "sum((g.product_uom_qty*coalesce(x.quantity,0.0)/gg.product_uom_qty)*coalesce(ap.factor,0.0)/coalesce(f.factor,1.0)) as qty_kg, \
            sum((g.product_uom_qty*coalesce(x.quantity,0.0)/gg.product_uom_qty)*coalesce(aq.factor,0.0)/coalesce(f.factor,1.0)) as qty_bale, \
            sum((g.product_uom_qty*coalesce(x.quantity,0.0)/gg.product_uom_qty)*coalesce(au.factor,0.0)/coalesce(f.factor,1.0)) as qty_unit, \
            sum(case when a.sale_type = 'local' and a.locale_sale_type = 'okb' then \
                    (coalesce(x.price_subtotal,0.0)+coalesce(x.tax_amount,0.0)) * \
                        case when coalesce(z2.name,'') = 'IDR' then \
                            case when coalesce(z.name,'') = 'IDR' then 1.0 / (coalesce(ak.rate,1.0) * coalesce(ai.rate,0.0)) \
                            else 1.0 / coalesce(ab.rate,1.0) end \
                        else 1.0 / coalesce(ab.rate,1.0) end \
                else coalesce(x.price_subtotal,0.0) * \
                    case when coalesce(z2.name,'') = 'IDR' then \
                        case when coalesce(z.name,'') = 'IDR' then 1.0 / (coalesce(ak.rate,1.0) * coalesce(ai.rate,0.0)) \
                        else 1.0 / coalesce(ab.rate,1.0) end \
                    else 1.0 / coalesce(ab.rate,1.0) end \
                end * (g.product_uom_qty/gg.product_uom_qty)) as gross_amount, \
            sum(case when a.sale_type = 'local' and a.locale_sale_type = 'okb' then \
                    (coalesce(x.price_subtotal,0.0)+coalesce(x.tax_amount,0.0)) * \
                        case when coalesce(z2.name,'') = 'IDR' then \
                            case when coalesce(z.name,'') = 'IDR' then 1.0 / coalesce(ao.rate,1.0) \
                            else coalesce(ad.rate,0.0) / coalesce(ao.rate,1.0) end \
                        else 1.0 / coalesce(ab.rate,1.0) end \
                else coalesce(x.price_subtotal,0.0) * \
                    case when coalesce(z2.name,'') = 'IDR' then \
                        case when coalesce(z.name,'') = 'IDR' then 1.0 / coalesce(ao.rate,1.0) \
                        else coalesce(ad.rate,0.0) / coalesce(ao.rate,1.0) end \
                    else 1.0 / coalesce(ab.rate,1.0) end \
                end * (g.product_uom_qty/gg.product_uom_qty)) as gross_amount_usd, \
            sum(case when a.sale_type = 'local' and a.locale_sale_type = 'okb' then \
                    coalesce(x.price_subtotal,0.0)+coalesce(x.tax_amount,0.0) \
                else coalesce(x.price_subtotal,0.0) \
                end * (g.product_uom_qty/gg.product_uom_qty)) as gross_amount_cury, \
            sum((g.product_uom_qty/gg.product_uom_qty) * coalesce(x.price_subtotal,0.0) * \
                case when coalesce(z2.name,'') = 'IDR' then \
                    case when coalesce(z.name,'') = 'IDR' then 1.0 / (coalesce(ak.rate,1.0) * coalesce(ai.rate,0.0)) \
                    else 1.0 / coalesce(ab.rate,1.0) end \
                else 1.0 / coalesce(ab.rate,1.0) end) as net_amount, \
            sum((g.product_uom_qty/gg.product_uom_qty) * coalesce(x.price_subtotal,0.0) * coalesce(ai.rate,0.0)) as net_amount_usd, \
            sum((g.product_uom_qty/gg.product_uom_qty) * coalesce(x.price_subtotal,0.0)) as net_amount_cury \
            from (  select g1.name,g1.date_done,g1.invoice_id,g2.sequence_line,g2.sale_line_id,g2.location_id, \
                        g2.location_dest_id,g2.product_id,g2.tracking_id,g2.invoice_line_id, \
                        sum(case g1.type \
                          when 'in' then g2.product_qty \
                          when 'out' then -g2.product_qty \
                          else 0 end) as product_uom_qty \
                    from stock_picking g1 \
                    inner join stock_move g2 on g1.id=g2.picking_id \
                    where g1.state='done' and g2.state='done' \
                        and (to_char(g1.date_done,'YYYY-MM-DD') between substring(%s,1,10) and substring(%s,1,10)) \
                        and coalesce(g1.sale_id,0) <> 0 \
                    group by g1.name,g1.date_done,g1.invoice_id,g2.sequence_line,g2.sale_line_id,g2.location_id, \
                        g2.location_dest_id,g2.product_id,g2.tracking_id,g2.invoice_line_id) g \
            inner join (select gg1.invoice_id,gg2.product_id, \
                        sum(case gg1.type \
                          when 'in' then gg2.product_qty \
                          when 'out' then -gg2.product_qty \
                          else 0 end) as product_uom_qty \
                    from stock_picking gg1 \
                    inner join stock_move gg2 on gg1.id=gg2.picking_id \
                    where gg1.state='done' and gg2.state='done' \
                        and (to_char(gg1.date_done,'YYYY-MM-DD') between substring(%s,1,10) and substring(%s,1,10)) \
                        and coalesce(gg1.sale_id,0) <> 0 and coalesce(gg2.sale_line_id,0) <> 0 \
                    group by gg1.invoice_id,gg2.product_id) gg on g.invoice_id = gg.invoice_id and g.product_id = gg.product_id \
            inner join sale_order_line b on g.product_id = b.product_id and g.sale_line_id = b.id \
            inner join sale_order a on b.order_id = a.id \
            inner join product_product c on g.product_id = c.id \
            inner join res_partner d on a.partner_id = d.id \
            left join (select * from stock_location where usage<>'view') u on g.location_id = u.id \
            left join (select * from stock_location where usage<>'view') u2 on g.location_dest_id = u2.id \
            left join account_invoice v on g.invoice_id = v.id \
            left join product_uom f on b.product_uom = f.id \
            left join mrp_blend_code q on c.blend_code = q.id \
            left join (select invoice_id,product_id,sum(quantity) as quantity,sum(price_subtotal) as price_subtotal,sum(tax_amount) as tax_amount \
                       from account_invoice_line \
                       where price_unit>0.0 \
                       group by invoice_id,product_id) x on g.invoice_id = x.invoice_id and g.product_id = x.product_id \
            left join res_currency z on v.currency_id = z.id \
            left join res_currency z2 on v.currency_tax_id = z2.id \
            left join (select aa1.id, aa1.currency_id, max(aa2.name) as curr_date \
                       from account_invoice aa1 \
                       inner join res_currency_rate aa2 on aa1.currency_id = aa2.currency_id \
                       where to_char(aa2.name,'YYYY-MM-DD') <= to_char(aa1.date_invoice,'YYYY-MM-DD') \
                       group by aa1.id,aa1.currency_id) aa on g.invoice_id = aa.id \
            left join res_currency_rate ab on aa.currency_id = ab.currency_id and aa.curr_date = ab.name \
            left join (select ac1.id, ac1.currency_id, max(ac2.name) as curr_date \
                       from account_invoice ac1 \
                       inner join res_currency_tax_rate ac2 on ac1.currency_id = ac2.currency_id \
                       where to_char(ac2.name,'YYYY-MM-DD') <= to_char(coalesce(ac1.tax_date,ac1.date_invoice),'YYYY-MM-DD') \
                       group by ac1.id,ac1.currency_id) ac on g.invoice_id = ac.id \
            left join res_currency_tax_rate ad on ac.currency_id = ad.currency_id and ac.curr_date = ad.name \
            left join (select ah1.id,ah2.currency_id,max(ah2.name) as curr_date \
                       from account_invoice ah1,res_currency_rate ah2,res_currency ah3 \
                       where to_char(ah2.name,'YYYY-MM-DD') <= to_char(ah1.date_invoice,'YYYY-MM-DD') and ah3.name = 'USD' and ah2.currency_id = ah3.id \
                       group by ah1.id,ah2.currency_id) ah on g.invoice_id = ah.id \
            left join res_currency_rate ai on ah.currency_id = ai.currency_id and ah.curr_date = ai.name \
            left join (select aj1.id,aj2.currency_id,max(aj2.name) as curr_date \
                       from account_invoice aj1,res_currency_tax_rate aj2,res_currency aj3 \
                       where to_char(aj2.name,'YYYY-MM-DD') <= to_char(aj1.date_invoice,'YYYY-MM-DD') and aj3.name = 'USD' and aj2.currency_id = aj3.id \
                       group by aj1.id,aj2.currency_id) aj on g.invoice_id = aj.id \
            left join res_currency_tax_rate ak on aj.currency_id = ak.currency_id and aj.curr_date = ak.name \
            left join (select al1.id,al2.currency_id,max(al2.name) as curr_date \
                       from account_invoice al1,res_currency_rate al2,res_currency al3 \
                       where to_char(al2.name,'YYYY-MM-DD') <= to_char(al1.date_invoice,'YYYY-MM-DD') and al3.name = 'IDR' and al2.currency_id = al3.id \
                       group by al1.id,al2.currency_id) al on g.invoice_id = al.id \
            left join res_currency_rate am on al.currency_id = am.currency_id and al.curr_date = am.name \
            left join (select an1.id,an2.currency_id,max(an2.name) as curr_date \
                       from account_invoice an1,res_currency_tax_rate an2,res_currency an3,res_company an4 \
                       where to_char(an2.name,'YYYY-MM-DD') <= to_char(an1.date_invoice,'YYYY-MM-DD') \
                       and an2.currency_id = an3.id and an3.id = an4.currency_id \
                       group by an1.id,an2.currency_id) an on g.invoice_id = an.id \
            left join res_currency_tax_rate ao on an.currency_id = ao.currency_id and an.curr_date = ao.name \
            left join (select category_id,min(factor) as factor \
                       from product_uom \
                       where name = 'KGS' \
                       group by category_id) ap on ap.category_id = f.category_id \
            left join (select category_id,min(factor) as factor \
                       from product_uom \
                       where name = 'BALES' \
                       group by category_id) aq on aq.category_id = f.category_id \
left join (select id,name,category_id,min(factor) as factor \
                       from product_uom \
                       where name not in ('BALES','KGS') \
                       group by id,name,category_id) au on au.id=b.product_uom\
            left join res_partner crp on v.consignee = crp.id \
            left join res_country trc on crp.country_id = trc.id "

        if sheet == 'customer':
            s = "select substring(coalesce(u.alias,u.name,''),1,3) as dept_id, \
                coalesce(d.partner_alias,d.name) as cust_name,au.name as uom, " + s1

            if data['form']['sale_type'] == 'export':
                self.cr.execute (s + " where u2.usage=%s \
                                       and a.goods_type = %s \
                                       and a.sale_type = %s \
                                       group by substring(coalesce(u.alias,u.name,''),1,3),coalesce(d.partner_alias,d.name),au.name \
                                       order by substring(coalesce(u.alias,u.name,''),1,3),coalesce(d.partner_alias,d.name)", 
                                  (data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['usage'],
                                    data['form']['goods_type'],
                                    data['form']['sale_type'],))
            else:
                self.cr.execute (s + " where u2.usage=%s \
                                       and a.goods_type = %s \
                                       and a.sale_type = %s \
                                       and a.locale_sale_type like %s \
                                       and v.currency_id = %s \
                                       group by substring(coalesce(u.alias,u.name,''),1,3),coalesce(d.partner_alias,d.name),au.name \
                                       order by substring(coalesce(u.alias,u.name,''),1,3),coalesce(d.partner_alias,d.name)", 
                                  (data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['usage'],
                                    data['form']['goods_type'],
                                    data['form']['sale_type'],
                                    data['form']['locale_sale_type'],
                                    data['form']['currency_id'][0],))
        elif sheet == 'product':
            s = "select substring(coalesce(u.alias,u.name,''),1,3) as dept_id, \
                coalesce(q.name,'') as blend, \
                c.default_code as prod_code, \
                c.name_template as prod_name,au.name as uom, " + s1

            if data['form']['sale_type'] == 'export':
                self.cr.execute (s + " where u2.usage=%s \
                                       and a.goods_type = %s \
                                       and a.sale_type = %s \
                                       group by substring(coalesce(u.alias,u.name,''),1,3),coalesce(q.name,''), \
                                       c.default_code,c.name_template,au.name \
                                       order by substring(coalesce(u.alias,u.name,''),1,3),coalesce(q.name,''), \
                                       c.default_code,c.name_template", 
                                  (data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['usage'],
                                    data['form']['goods_type'],
                                    data['form']['sale_type'],))
            else:
                self.cr.execute (s + " where u2.usage=%s \
                                       and a.goods_type = %s \
                                       and a.sale_type = %s \
                                       and a.locale_sale_type like %s \
                                       and v.currency_id = %s \
                                       group by substring(coalesce(u.alias,u.name,''),1,3),coalesce(q.name,''), \
                                       c.default_code,c.name_template,au.name \
                                       order by substring(coalesce(u.alias,u.name,''),1,3),coalesce(q.name,''), \
                                       c.default_code,c.name_template", 
                                  (data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['usage'],
                                    data['form']['goods_type'],
                                    data['form']['sale_type'],
                                    data['form']['locale_sale_type'],
                                    data['form']['currency_id'][0],))
        elif sheet == 'country':
            s = "select (case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end) as dest_country_name, \
                coalesce(d.partner_alias,d.name) as cust_name,au.name as uom, " + s1

            if data['form']['sale_type'] == 'export':
                self.cr.execute (s + " where u2.usage=%s \
                                       and a.goods_type = %s \
                                       and a.sale_type = %s \
                                       group by case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end,coalesce(d.partner_alias,d.name),au.name \
                                       order by case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end,coalesce(d.partner_alias,d.name)", 
                                  (data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['usage'],
                                    data['form']['goods_type'],
                                    data['form']['sale_type'],))
            else:
                self.cr.execute (s + " where u2.usage=%s \
                                       and a.goods_type = %s \
                                       and a.sale_type = %s \
                                       and a.locale_sale_type like %s \
                                       and v.currency_id = %s \
                                       group by case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end,coalesce(d.partner_alias,d.name),au.name \
                                       order by case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end,coalesce(d.partner_alias,d.name)", 
                                  (data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['usage'],
                                    data['form']['goods_type'],
                                    data['form']['sale_type'],
                                    data['form']['locale_sale_type'],
                                    data['form']['currency_id'][0],))
        else:
            s = "select substring(coalesce(u.alias,u.name,''),1,3) as dept_id, \
                to_char(g.date_done,'DD/MM/YYYY') as do_date_dmy,au.name as uom, " + s1

            if data['form']['sale_type'] == 'export':
                self.cr.execute (s + " where u2.usage=%s \
                                       and a.goods_type = %s \
                                       and a.sale_type = %s \
                                       group by substring(coalesce(u.alias,u.name,''),1,3),to_char(g.date_done,'DD/MM/YYYY'),au.name \
                                       order by substring(coalesce(u.alias,u.name,''),1,3),to_char(g.date_done,'DD/MM/YYYY')", 
                                  (data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['usage'],
                                    data['form']['goods_type'],
                                    data['form']['sale_type'],))
            else:
                self.cr.execute (s + " where u2.usage=%s \
                                       and a.goods_type = %s \
                                       and a.sale_type = %s \
                                       and a.locale_sale_type like %s \
                                       and v.currency_id = %s \
                                       group by substring(coalesce(u.alias,u.name,''),1,3),to_char(g.date_done,'DD/MM/YYYY'),au.name \
                                       order by substring(coalesce(u.alias,u.name,''),1,3),to_char(g.date_done,'DD/MM/YYYY')", 
                                  (data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['usage'],
                                    data['form']['goods_type'],
                                    data['form']['sale_type'],
                                    data['form']['locale_sale_type'],
                                    data['form']['currency_id'][0],))
        
        res = self.cr.dictfetchall()
        return res