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

class ReportSalesOrder(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(ReportSalesOrder, self).__init__(cr, uid, name, context=context)
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
        usage =data['form']['usage'] == 'internal' and 'RETURN ' or ''
        stitle = stitle + 'SALES ' + usage + 'STATEMENT - '
        if sheet == 'customer':
            stitle = stitle + 'CUSTOMER WISE'
        elif sheet == 'product':
            stitle = stitle + 'PRODUCT WISE'
        elif sheet == 'date':
            stitle = stitle + 'DATE WISE'
        elif sheet == 'invoice':
            stitle = stitle + 'INVOICE WISE'
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

    def _uom_to_bales(self,qty,uom_source):
        cr = self.cr
        uid = self.uid
        bale_obj = self.pool.get('product.uom').search(cr,uid,[('name','=','BALES')])
        for bale_ids in bale_obj:
            category_id=self.pool.get('product.uom').browse(cr,uid,bale_ids).category_id.id
        print category_id,"dadadadadada"
        for y in self.pool.get('product.uom').browse(cr,uid,[uom_source]):
            uom_source_id=y.category_id.id
        print uom_source_id,"glalalalalala"
        if category_id==uom_source_id:
            qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, qty, to_uom_id=bale_obj and bale_obj[0] or False)
        else:
            qty_result=0.0        
        print qty_result,"sbsbbabbabssabasbsbsabsabsbsbsbs"
        return round(qty_result,4)

    def _uom_to_kgs(self,qty,uom_source):
        cr = self.cr
        uid = self.uid
        bale_obj = self.pool.get('product.uom').search(cr,uid,[('name','=','KGS')])
        for bale_ids in bale_obj:
            category_id=self.pool.get('product.uom').browse(cr,uid,bale_ids).category_id.id
        print category_id,'dododododododododod'
        for y in self.pool.get('product.uom').browse(cr,uid,[uom_source]):
            uom_source_id=y.category_id.id
        print uom_source_id,"lolllooololooooooooooooooooooooooo"
        if category_id==uom_source_id:
            qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, qty, to_uom_id=bale_obj and bale_obj[0] or False)
        else:
            qty_result=0.0
        print qty_result,"brobrobrobroooooooooooooooooooooooooooooooo"
        return round(qty_result,4)

    def _get_qtyshipment(self,soline_id,productline_id):
        cr=self.cr
        uid=self.uid
        context=None
        stockmove_obj=self.pool.get('stock.move')
        stockmove_ids=stockmove_obj.search(cr,uid,[('sale_line_id','=',soline_id),('product_id','=',productline_id)])
        qty_shipment=0.00
        if stockmove_ids:
            for moveline in stockmove_ids:
            # qty_received=self.pool.get('stock.move').browse(cr,uid,move_line,context=context).product_qty
                qty_shipment=stockmove_obj.browse(cr,uid,moveline,context=context).product_qty
        return qty_shipment


    def _uom_to_base(self,data,qty,uom_source):
        cr = self.cr
        uid = self.uid
        if data['form']['goods_type'] == 'finish_others' or data['form']['goods_type'] == 'waste' or data['form']['goods_type']=='asset':
          uom_base = 'KGS'
        elif data['form']['sale_type'] == 'export' or data['form']['sale_type'] == 'local':
          uom_base = 'BALES'
        else:
          uom_base = 'KGS'
        base_obj = self.pool.get('product.uom').search(cr,uid,[('name','=',uom_base)])
        for base_ids in base_obj:
            category_id=self.pool.get('product.uom').browse(cr,uid,base_ids).category_id.id
        print category_id,"nananananananananananananan"
        print uom_source,"kakakakka"
        for y in self.pool.get('product.uom').browse(cr, uid, [uom_source]):
            cateid_uom=y.category_id.id
        print cateid_uom,"hahahahahahaha"
        if category_id==cateid_uom:
            qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, qty, to_uom_id=base_obj and base_obj[0] or False)
            # print qty_result,"lalalalalalalalalalalalalalalalalalala"
        else:
            qty_result=0.0
        print qty_result,"lalalalalalalalalalalalalalalalalalala"
        return round(qty_result,4)

    def _price_per_bales(self,price,uom_source):
        cr = self.cr
        uid = self.uid
        bale = self.pool.get('product.uom').search(cr,uid,[('name','=','BALES')])
        qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, 1000.0, to_uom_id=bale and bale[0] or False)
        if qty_result>0:
          price_result = price*1000.0/qty_result 
        else:
          price_result = price 
        return round(price_result,2)

    def _price_per_kgs(self,price,uom_source):
        cr = self.cr
        uid = self.uid
        bale_obj = self.pool.get('product.uom').search(cr,uid,[('name','=','KGS')])
        for bale_ids in bale_obj:
            category_id=self.pool.get('product.uom').browse(cr,uid,bale_ids).category_id.id
        print category_id,"xxxlxaxxlakxxkaaxxalxa"
        for y in self.pool.get('product.uom').browse(cr,uid,[uom_source]):
            uom_source_id=y.category_id.id
        print uom_source_id,'vavavavavavavavavavvavava'
        if category_id==uom_source_id:
            qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, 1000.0, to_uom_id=bale_obj and bale_obj[0] or False)
        else:
            qty_result=0.0
        if qty_result>0:
          price_result = price*1000.0/qty_result 
        else:
          price_result = price 
        return round(price_result,2)

    def _price_per_base(self,data,price,uom_source):
        cr = self.cr
        uid = self.uid
        if data['form']['goods_type'] == 'finish_others' or data['form']['goods_type'] == 'waste' or data['form']['goods_type'] == 'asset':
          uom_base = 'KGS'
        elif data['form']['sale_type'] == 'export' or data['form']['sale_type'] == 'local':
          uom_base = 'BALES'
        else:
          uom_base = 'KGS'
        base_obj = self.pool.get('product.uom').search(cr,uid,[('name','=',uom_base)])
        for base_ids in base_obj:
            category_id=self.pool.get('product.uom').browse(cr,uid,base_ids).category_id.id
        print category_id,"statststststststs"
        for y in self.pool.get('product.uom').browse(cr,uid,[uom_source]):
            uom_source_id=y.category_id.id
        print uom_source_id,"dgdgdgadagdgagdgaggag"
        if category_id==uom_source_id:
            qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, 1000.0, to_uom_id=base_obj and base_obj[0] or False)
        else:
            qty_result=0.0

        if qty_result>0:
          price_result = price*1000.0/qty_result 
        else:
          price_result = price 
        return round(price_result,2)
        
    def _get_object(self,data):
        obj_data=self.pool.get(data['model']).browse(self.cr,self.uid,[data['form']['id']])
        return obj_data
    
    def _get_goods_type(self,data,context=None):
        if data['form']['goods_type'] == 'finish':
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
                          left join res_partner b on a.partner_id = b.id \
                          where a.id=1")

        res = self.cr.fetchone()
        return res

    def _get_base_currency(self,context=None):
        self.cr.execute ("select a.currency_id,a.tax_base_currency, \
                          coalesce(b.name,'') as currency_name, \
                          coalesce(c.name,'') as tax_base_currency_name \
                          from res_company a \
                          left join res_currency b on a.currency_id = b.id \
                          left join res_currency c on a.tax_base_currency = c.id \
                          where a.id=1")

        res = self.cr.dictfetchall()
        return res

    def _get_view(self,data,sheet,context=None):
        s = "select coalesce(u.alias,u.name,'') as loc_name, \
            g.name as do_name, \
            to_char(g.date_done,'YYYY-MM-DD') as do_date, \
            to_char(g.date_done,'DD/MM/YYYY') as do_date_dmy, \
            coalesce(w.nomor_urut,'') as tax_invc, \
            v.internal_number as invoice_no, \
            coalesce(v.peb_number,'') as peb_no, \
            coalesce(v.kode_transaksi_faktur_pajak,'') || '.' || coalesce(w.name,'') as tax_no, \
            coalesce(d.partner_code,'') as cust_code, \
            coalesce(d.partner_alias,d.name) as cust_name, \
            c.default_code as prod_code, \
            c.name_template as prod_name, \
            coalesce(b.sequence_line,a.name) as contract_no, \
            sum(g.product_uom_qty*coalesce(x.quantity,0.0)/gg.product_uom_qty) as product_uom_qty, \
            b.product_uom, \
            coalesce(z.name,'') as curr_name, \
            coalesce(y.tax_name,'') as tax_name, \
            coalesce(i.name,'') as payment_term_name, \
            coalesce(b.est_delivery_date,a.max_est_delivery_date) as sale_order_lsd, \
            coalesce(q.name,'') as blend, \
            (case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end) as count_name, \
            coalesce(b.sequence_line,a.name) as delivery_ref, \
            a.date_order, \
            track.tracking as tracking_name, \
            \
            round(avg(round(case when coalesce(xx.quantity,x.quantity,0.0)>0.0 then \
                                coalesce(xx.price_subtotal,x.price_subtotal,0.0)/coalesce(xx.quantity,x.quantity,1.0) \
                            else 0.0 end,2)),2) as cury_net_price, \
            round(avg(round(case when coalesce(xx.quantity,x.quantity,0.0)>0.0 then \
                                (coalesce(xx.price_subtotal,x.price_subtotal,0.0)/coalesce(xx.quantity,x.quantity,0.0)) * \
                                case when coalesce(z2.name,'') = 'IDR' then \
                                    case when coalesce(z.name,'') = 'IDR' then \
                                        1.0/coalesce(ao.rate,1.0) \
                                    else coalesce(ad.rate,0.0) / coalesce(ao.rate,1.0) end \
                                else 1.0/coalesce(ab.rate,1.0) end \
                            else 0.0 end,2)),2) as net_price, \
            avg(coalesce(y.tax_percent,0.0)) as tax_percent, \
            round(avg(round(coalesce(xx.price_unit,x.price_unit,0.0),2)),2) as cury_sell_price, \
            round(avg(round( coalesce(xx.price_unit,x.price_unit,0.0) * \
                        case when coalesce(z2.name,'') = 'IDR' then \
                            case when coalesce(z.name,'') = 'IDR' then 1.0/coalesce(ao.rate,1.0) \
                            else coalesce(ad.rate,0.0) / coalesce(ao.rate,1.0) end \
                        else 1.0/coalesce(ab.rate,1.0) end,2)),2) as sell_price, \
            avg(coalesce(ak.rate,0.0)) as kmk_rate, \
            round(avg(round( coalesce(xx.price_unit,x.price_unit,0.0) * \
                case when coalesce(z2.name,'') = 'IDR' then \
                    case when coalesce(z.name,'') = 'IDR' then 1.0 \
                    else coalesce(ak.rate,0.0) * coalesce(ai.rate,0.0) / coalesce(ab.rate,1.0) end \
                else coalesce(am.rate,0.0) / coalesce(ab.rate,1.0) end,2)),2) as sell_price_idr, \
            round(avg(round(coalesce(xx.price_unit,x.price_unit,0.0) * \
                case when coalesce(z2.name,'') = 'IDR' then \
                    case when coalesce(z.name,'') = 'IDR' then 1.0 / coalesce(ak.rate,1.0) \
                    else coalesce(ai.rate,0.0) / coalesce(ab.rate,1.0) end \
                else coalesce(ai.rate,0.0) / coalesce(ab.rate,1.0) end,2)),2) as sell_price_usd, \
            round(sum((g.product_uom_qty/gg.product_uom_qty) * \
                coalesce(x.price_subtotal,0.0)),2) as cury_net_amount, \
            round(sum((g.product_uom_qty/gg.product_uom_qty) * \
                round(coalesce(x.price_subtotal,0.0) * \
                case when coalesce(z2.name,'') = 'IDR' then \
                    case when coalesce(z.name,'') = 'IDR' then 1.0 / coalesce(ao.rate,1.0) \
                    else coalesce(ad.rate,0.0) / coalesce(ao.rate,1.0) end \
                else 1.0 / coalesce(ab.rate,1.0) end,2)),2) as net_amount, \
            round(sum((g.product_uom_qty/gg.product_uom_qty) * \
                round(coalesce(x.tax_amount,0.0),2)),2) as cury_tax_amount, \
            round(sum((g.product_uom_qty/gg.product_uom_qty) * \
                round(coalesce(x.tax_amount,0.0) * \
                case when coalesce(z2.name,'') = 'IDR' then \
                    case when coalesce(z.name,'') = 'IDR' then 1.0 / coalesce(ao.rate,1.0) \
                    else coalesce(ad.rate,0.0) / coalesce(ao.rate,1.0) end \
                else 1.0 / coalesce(ab.rate,1.0) end,2)),2) as tax_amount, \
            round(sum((g.product_uom_qty/gg.product_uom_qty) * \
                (coalesce(x.price_subtotal,0.0) + coalesce(x.tax_amount,0.0))),2) as cury_tot_amount, \
            round(sum((g.product_uom_qty/gg.product_uom_qty) * \
                round((coalesce(x.price_subtotal,0.0)+coalesce(x.tax_amount,0.0)) * \
                case when coalesce(z2.name,'') = 'IDR' then \
                    case when coalesce(z.name,'') = 'IDR' then 1.0 / coalesce(ao.rate,1.0) \
                    else coalesce(ad.rate,0.0) / coalesce(ao.rate,1.0) end \
                else 1.0 / coalesce(ab.rate,1.0) end,2)),2) as tot_amount, \
            round(sum((g.product_uom_qty/gg.product_uom_qty) * \
                round(  case when coalesce(z2.name,'') = 'IDR' then \
                            case when coalesce(z.name,'') = 'IDR' then 1.0 \
                            else coalesce(ak.rate,0.0) end \
                        else 1.0 end * \
                        round(  (coalesce(x.price_subtotal,0.0)+coalesce(x.tax_amount,0.0)) * \
                                case when coalesce(z2.name,'') = 'IDR' then \
                                    case when coalesce(z.name,'') = 'IDR' then 1.0 \
                                    else coalesce(ai.rate,0.0) / coalesce(ab.rate,1.0) end \
                                else coalesce(am.rate,0.0) / coalesce(ab.rate,1.0) end,2),2)),2) as tot_amount_idr, \
            sum(case when  a.sale_type = 'export' then  \
                            round(((g.product_uom_qty*coalesce(x.quantity,0.0)/gg.product_uom_qty) *(coalesce(xx.price_unit,x.price_unit,0.0))),2) \
                    when   a.sale_type = 'local' then \
                            round(((g.product_uom_qty/gg.product_uom_qty) * \
                            round((coalesce(x.price_subtotal,0.0)+coalesce(x.tax_amount,0.0)) * \
                            case when coalesce(z2.name,'') = 'IDR' then \
                            case when coalesce(z.name,'') = 'IDR' then 1.0 / coalesce(ak.rate,1.0) \
                            else coalesce(ai.rate,0.0) / coalesce(ab.rate,1.0) end \
                            else coalesce(ai.rate,0.0) / coalesce(ab.rate,1.0) end,2)),2) \
            end) as tot_amount_usd, \
            round(sum(  case when a.sale_type = 'local' and a.locale_sale_type = 'ikb' then 0.0 \
                        else (g.product_uom_qty/gg.product_uom_qty) * \
                            round(  case when coalesce(z2.name,'') = 'IDR' then \
                                        case when coalesce(z.name,'') = 'IDR' then 1.0 \
                                        else coalesce(ak.rate,0.0) end \
                                    else 1.0 end * \
                                    round(  coalesce(x.price_subtotal,0.0) * \
                                            case when coalesce(z2.name,'') = 'IDR' then \
                                                case when coalesce(z.name,'') = 'IDR' then 1.0 \
                                                else coalesce(ai.rate,0.0) / coalesce(ab.rate,1.0) end \
                                            else coalesce(am.rate,0.0) / coalesce(ab.rate,1.0) end,2),2) \
                        end),2) as dpp_npet, \
            round(sum(  case when a.sale_type = 'local' and a.locale_sale_type = 'ikb' then \
                            (g.product_uom_qty/gg.product_uom_qty) * \
                            round(  case when coalesce(z2.name,'') = 'IDR' then \
                                        case when coalesce(z.name,'') = 'IDR' then 1.0 \
                                        else coalesce(ak.rate,0.0) end \
                                    else 1.0 end * \
                                    round(  coalesce(x.price_subtotal,0.0) * \
                                            case when coalesce(z2.name,'') = 'IDR' then \
                                                case when coalesce(z.name,'') = 'IDR' then 1.0 \
                                                else coalesce(ai.rate,0.0) / coalesce(ab.rate,1.0) end \
                                            else coalesce(am.rate,0.0) / coalesce(ab.rate,1.0) end,2),2) \
                        else 0.0 end),2) as dpp_pet, \
            round(sum(  case when a.sale_type = 'local' and a.locale_sale_type = 'ikb' then 0.0 \
                        else 0.1 * (g.product_uom_qty/gg.product_uom_qty) * \
                            round(  case when coalesce(z2.name,'') = 'IDR' then \
                                        case when coalesce(z.name,'') = 'IDR' then 1.0 \
                                        else coalesce(ak.rate,0.0) end \
                                    else 1.0 end * \
                                    round(  coalesce(x.price_subtotal,0.0) * \
                                            case when coalesce(z2.name,'') = 'IDR' then \
                                                case when coalesce(z.name,'') = 'IDR' then 1.0 \
                                                else coalesce(ai.rate,0.0) / coalesce(ab.rate,1.0) end \
                                            else coalesce(am.rate,0.0) / coalesce(ab.rate,1.0) end,2),2) \
                        end),2) as tax_npet, \
            0.0 as tax_pet, \
            (case when a.sale_type = 'local' then 'Indonesia' \
            else coalesce(trc.name,'') end) as dest_country_name, \
            f.name as uom\
            from (  select g1.name,g1.date_done,g1.invoice_id,g2.sequence_line,g2.sale_line_id, \
                        g2.location_id,g2.location_dest_id,g2.product_id,g2.tracking_id,g2.invoice_line_id, \
                        sum(case g1.type \
                          when 'in' then g2.product_qty \
                          when 'out' then -g2.product_qty \
                          else 0 end) as product_uom_qty \
                    from stock_picking g1 \
                    inner join stock_move g2 on g1.id=g2.picking_id \
                    where g1.state='done' and g2.state='done' \
                        and (to_char(g1.date_done,'YYYY-MM-DD') between substring(%s,1,10) and substring(%s,1,10)) \
                        and coalesce(g1.sale_id,0) <> 0 and coalesce(g2.sale_line_id,0) <> 0 \
                    group by g1.name,g1.date_done,g1.invoice_id,g2.sequence_line,g2.sale_line_id, \
                        g2.location_id,g2.location_dest_id,g2.product_id,g2.tracking_id,g2.invoice_line_id) g \
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
            inner join (select * from sale_order where state <> 'cancel') a on b.order_id = a.id \
            inner join product_product c on g.product_id = c.id \
            left join (select * from stock_location where usage<>'view') u on g.location_id = u.id \
            left join (select * from stock_location where usage<>'view') u2 on g.location_dest_id = u2.id \
            left join (select * from account_invoice where state <> 'cancel') v on g.invoice_id = v.id \
            inner join res_partner d on v.partner_id = d.id \
            left join nomor_faktur_pajak w on v.nomor_faktur_id = w.id \
            left join product_uom f on b.product_uom = f.id \
            left join (select invoice_id,product_id,max(id) as id,avg(price_unit) as price_unit,sum(quantity) as quantity,sum(price_subtotal) as price_subtotal,sum(tax_amount) as tax_amount \
                       from account_invoice_line \
                       where price_unit>0.0 \
                       group by invoice_id,product_id) x on g.invoice_id = x.invoice_id and g.product_id = x.product_id \
            left join (select y1.invoice_line_id, sum(y2.amount*100.0*y2.tax_sign) as tax_percent, string_agg(to_char(y2.amount*100.0*y2.tax_sign,'999D99S'),' + ') as tax_name \
                       from account_invoice_line_tax y1 \
                       inner join account_tax y2 on y1.tax_id = y2.id \
                       group by y1.invoice_line_id) y on x.id = y.invoice_line_id \
            left join account_invoice_line xx on g.invoice_id = xx.invoice_id and g.product_id = xx.product_id and g.invoice_line_id = xx.id \
            left join res_currency z on v.currency_id = z.id \
            left join res_currency z2 on v.currency_tax_id = z2.id \
            left join mrp_blend_code q on c.blend_code = q.id \
            left join account_payment_term i on a.payment_term = i.id \
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
            left join stock_tracking ae on g.tracking_id = ae.id \
            left join (select ah1.id,ah2.currency_id,max(ah2.name) as curr_date \
                       from account_invoice ah1,res_currency_rate ah2,res_currency ah3 \
                       where to_char(ah2.name,'YYYY-MM-DD') <= to_char(ah1.date_invoice,'YYYY-MM-DD') and ah3.name = 'USD' and ah2.currency_id = ah3.id \
                       group by ah1.id,ah2.currency_id) ah on g.invoice_id = ah.id \
            left join res_currency_rate ai on ah.currency_id = ai.currency_id and ah.curr_date = ai.name \
            left join (select aj1.id,aj2.currency_id,max(aj2.name) as curr_date \
                       from account_invoice aj1,res_currency_tax_rate aj2,res_currency aj3 \
                       where to_char(aj2.name,'YYYY-MM-DD') <= to_char(coalesce(aj1.tax_date,aj1.date_invoice),'YYYY-MM-DD') and aj3.name = 'USD' and aj2.currency_id = aj3.id \
                       group by aj1.id,aj2.currency_id) aj on g.invoice_id = aj.id \
            left join res_currency_tax_rate ak on aj.currency_id = ak.currency_id and aj.curr_date = ak.name \
            left join (select al1.id,al2.currency_id,max(al2.name) as curr_date \
                       from account_invoice al1,res_currency_rate al2,res_currency al3 \
                       where to_char(al2.name,'YYYY-MM-DD') <= to_char(al1.date_invoice,'YYYY-MM-DD') and al3.name = 'IDR' and al2.currency_id = al3.id \
                       group by al1.id,al2.currency_id) al on g.invoice_id = al.id \
            left join res_currency_rate am on al.currency_id = am.currency_id and al.curr_date = am.name \
            left join (select an1.id,an2.currency_id,max(an2.name) as curr_date \
                       from account_invoice an1,res_currency_tax_rate an2,res_currency an3,res_company an4 \
                       where to_char(an2.name,'YYYY-MM-DD') <= to_char(coalesce(an1.tax_date,an1.date_invoice),'YYYY-MM-DD') \
                       and an2.currency_id = an3.id and an3.id = an4.currency_id \
                       group by an1.id,an2.currency_id) an on g.invoice_id = an.id \
            left join res_currency_tax_rate ao on an.currency_id = ao.currency_id and an.curr_date = ao.name \
            left join res_partner crp on v.consignee = crp.id \
            left join res_country trc on crp.country_id = trc.id \
            inner join ( \
                    select a.sale_line_id,string_agg(a.lot_no,',') as tracking from (\
                    select  smo.sale_line_id,coalesce(stg.alias,stg.name) as lot_no  \
                                    from stock_picking stp inner join stock_move smo on stp.id=smo.picking_id \
                                    left outer join stock_tracking stg on smo.tracking_id=stg.id \
                                    \
                                        where coalesce(smo.sale_line_id,0) <> 0 \
                                        \
                                        group by smo.sale_line_id, coalesce(stg.alias,stg.name) \
                                        ) a \
                                        group by a.sale_line_id \
            ) track on track.sale_line_id=g.sale_line_id \
            "

        if sheet == 'customer':
            if data['form']['sale_type'] == 'export':
                self.cr.execute (s + " where u2.usage=%s and \
                                       a.goods_type = %s \
                                       and a.sale_type = %s \
                                       group by coalesce(u.alias,u.name,''),coalesce(d.partner_code,''),coalesce(d.partner_alias,d.name),g.name,to_char(g.date_done,'YYYY-MM-DD'), \
                                       to_char(g.date_done,'DD/MM/YYYY'),v.internal_number,coalesce(v.peb_number,''),coalesce(w.nomor_urut,''),coalesce(q.name,''), \
                                       case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end, \
                                       c.sd_type,coalesce(b.est_delivery_date,a.max_est_delivery_date), \
                                       cast(coalesce(b.sequence_line_1_moved1,'0') as int), \
                                       coalesce(b.sequence_line,a.name),a.date_order, \
                                       track.tracking, \
                                       coalesce(v.kode_transaksi_faktur_pajak,'') || '.' || coalesce(w.name,''), \
                                       c.default_code,c.name_template,a.name,b.product_uom, \
                                       coalesce(z.name,''),coalesce(y.tax_name,''),coalesce(i.name,''), \
                                       case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end,f.name \
                                       order by coalesce(u.alias,u.name,''),coalesce(d.partner_alias,d.name),g.name,to_char(g.date_done,'YYYY-MM-DD'), \
                                       v.internal_number,coalesce(w.nomor_urut,''),coalesce(q.name,''), \
                                       case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end, \
                                       c.sd_type,coalesce(b.est_delivery_date,a.max_est_delivery_date), \
                                       cast(coalesce(b.sequence_line_1_moved1,'0') as int), \
                                       coalesce(b.sequence_line,a.name),a.date_order, \
                                       coalesce(v.kode_transaksi_faktur_pajak,'') || '.' || coalesce(w.name,''), \
                                       c.default_code,c.name_template,a.name,b.product_uom, \
                                       coalesce(z.name,''),coalesce(y.tax_name,''),coalesce(i.name,''), \
                                       case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end", 
                                  (data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['usage'],
                                    data['form']['goods_type'],
                                    data['form']['sale_type'],))
            elif data['form']['sale_type'] == 'local':
                self.cr.execute (s + " where u2.usage=%s and \
                                       a.goods_type = %s \
                                       and a.sale_type = %s \
                                       and a.locale_sale_type like %s \
                                       and v.currency_id = %s \
                                       group by coalesce(u.alias,u.name,''),coalesce(d.partner_code,''),coalesce(d.partner_alias,d.name),g.name,to_char(g.date_done,'YYYY-MM-DD'), \
                                       to_char(g.date_done,'DD/MM/YYYY'),v.internal_number,coalesce(v.peb_number,''),coalesce(w.nomor_urut,''),coalesce(q.name,''), \
                                       case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end, \
                                       c.sd_type,coalesce(b.est_delivery_date,a.max_est_delivery_date), \
                                       cast(coalesce(b.sequence_line_1_moved1,'0') as int), \
                                       coalesce(b.sequence_line,a.name),a.date_order, \
                                       track.tracking, \
                                       coalesce(v.kode_transaksi_faktur_pajak,'') || '.' || coalesce(w.name,''), \
                                       c.default_code,c.name_template,a.name,b.product_uom, \
                                       coalesce(z.name,''),coalesce(y.tax_name,''),coalesce(i.name,''), \
                                       case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end,f.name \
                                       order by coalesce(u.alias,u.name,''),coalesce(d.partner_alias,d.name),g.name,to_char(g.date_done,'YYYY-MM-DD'), \
                                       v.internal_number,coalesce(w.nomor_urut,''),coalesce(q.name,''), \
                                       case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end, \
                                       c.sd_type,coalesce(b.est_delivery_date,a.max_est_delivery_date), \
                                       cast(coalesce(b.sequence_line_1_moved1,'0') as int), \
                                       coalesce(b.sequence_line,a.name),a.date_order, \
                                       coalesce(v.kode_transaksi_faktur_pajak,'') || '.' || coalesce(w.name,''), \
                                       c.default_code,c.name_template,a.name,b.product_uom, \
                                       coalesce(z.name,''),coalesce(y.tax_name,''),coalesce(i.name,''), \
                                       case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end", 
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
            if data['form']['sale_type'] == 'export':
                self.cr.execute (s + " where u2.usage=%s and \
                                       a.goods_type = %s \
                                       and a.sale_type = %s \
                                       group by coalesce(u.alias,u.name,''),coalesce(q.name,''), \
                                       case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end, \
                                       c.sd_type,g.name,to_char(g.date_done,'YYYY-MM-DD'),to_char(g.date_done,'DD/MM/YYYY'), \
                                       v.internal_number,coalesce(v.peb_number,''),coalesce(w.nomor_urut,''), \
                                       coalesce(b.est_delivery_date,a.max_est_delivery_date), \
                                       cast(coalesce(b.sequence_line_1_moved1,'0') as int), \
                                       coalesce(b.sequence_line,a.name),coalesce(d.partner_code,''),coalesce(d.partner_alias,d.name),a.date_order, \
                                       track.tracking, \
                                       coalesce(v.kode_transaksi_faktur_pajak,'') || '.' || coalesce(w.name,''), \
                                       c.default_code,c.name_template,a.name,b.product_uom, \
                                       coalesce(z.name,''),coalesce(y.tax_name,''),coalesce(i.name,''), \
                                       case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end,f.name \
                                       order by coalesce(u.alias,u.name,''),coalesce(q.name,''), \
                                       case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end, \
                                       c.sd_type,g.name,to_char(g.date_done,'YYYY-MM-DD'), \
                                       v.internal_number,coalesce(w.nomor_urut,''), \
                                       coalesce(b.est_delivery_date,a.max_est_delivery_date), \
                                       cast(coalesce(b.sequence_line_1_moved1,'0') as int), \
                                       coalesce(b.sequence_line,a.name),coalesce(d.partner_alias,d.name),a.date_order, \
                                       coalesce(v.kode_transaksi_faktur_pajak,'') || '.' || coalesce(w.name,''), \
                                       c.default_code,c.name_template,a.name,b.product_uom, \
                                       coalesce(z.name,''),coalesce(y.tax_name,''),coalesce(i.name,''), \
                                       case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end", 
                                  (data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['usage'],
                                    data['form']['goods_type'],
                                    data['form']['sale_type'],))
            elif data['form']['sale_type'] == 'local':
                self.cr.execute (s + " where u2.usage=%s and \
                                       a.goods_type = %s \
                                       and a.sale_type = %s \
                                       and a.locale_sale_type like %s \
                                       and v.currency_id = %s \
                                       group by coalesce(u.alias,u.name,''),coalesce(q.name,''), \
                                       case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end, \
                                       c.sd_type,g.name,to_char(g.date_done,'YYYY-MM-DD'),to_char(g.date_done,'DD/MM/YYYY'), \
                                       v.internal_number,coalesce(v.peb_number,''),coalesce(w.nomor_urut,''), \
                                       coalesce(b.est_delivery_date,a.max_est_delivery_date), \
                                       cast(coalesce(b.sequence_line_1_moved1,'0') as int), \
                                       coalesce(b.sequence_line,a.name),coalesce(d.partner_code,''),coalesce(d.partner_alias,d.name),a.date_order, \
                                       track.tracking, \
                                       coalesce(v.kode_transaksi_faktur_pajak,'') || '.' || coalesce(w.name,''), \
                                       c.default_code,c.name_template,a.name,b.product_uom, \
                                       coalesce(z.name,''),coalesce(y.tax_name,''),coalesce(i.name,''), \
                                       case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end,f.name \
                                       order by coalesce(u.alias,u.name,''),coalesce(q.name,''), \
                                       case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end, \
                                       c.sd_type,g.name,to_char(g.date_done,'YYYY-MM-DD'), \
                                       v.internal_number,coalesce(w.nomor_urut,''), \
                                       coalesce(b.est_delivery_date,a.max_est_delivery_date), \
                                       cast(coalesce(b.sequence_line_1_moved1,'0') as int), \
                                       coalesce(b.sequence_line,a.name),coalesce(d.partner_alias,d.name),a.date_order, \
                                       coalesce(v.kode_transaksi_faktur_pajak,'') || '.' || coalesce(w.name,''), \
                                       c.default_code,c.name_template,a.name,b.product_uom, \
                                       coalesce(z.name,''),coalesce(y.tax_name,''),coalesce(i.name,''), \
                                       case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end", 
                                  (data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['usage'],
                                    data['form']['goods_type'],
                                    data['form']['sale_type'],
                                    data['form']['locale_sale_type'],
                                    data['form']['currency_id'][0],))
        elif sheet == 'date':
            if data['form']['sale_type'] == 'export':
                self.cr.execute (s + " where u2.usage=%s and \
                                       a.goods_type = %s \
                                       and a.sale_type = %s \
                                       group by coalesce(u.alias,u.name,''),g.name,to_char(g.date_done,'YYYY-MM-DD'), \
                                       to_char(g.date_done,'DD/MM/YYYY'),v.internal_number,coalesce(v.peb_number,''),coalesce(w.nomor_urut,''),coalesce(q.name,''), \
                                       case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end, \
                                       c.sd_type,coalesce(b.est_delivery_date,a.max_est_delivery_date), \
                                       cast(coalesce(b.sequence_line_1_moved1,'0') as int), \
                                       coalesce(b.sequence_line,a.name),coalesce(d.partner_code,''),coalesce(d.partner_alias,d.name),a.date_order, \
                                       track.tracking, \
                                       coalesce(v.kode_transaksi_faktur_pajak,'') || '.' || coalesce(w.name,''), \
                                       c.default_code,c.name_template,a.name,b.product_uom, \
                                       coalesce(z.name,''),coalesce(y.tax_name,''),coalesce(i.name,''), \
                                       case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end ,f.name\
                                       order by coalesce(u.alias,u.name,''),g.name,to_char(g.date_done,'YYYY-MM-DD'), \
                                       v.internal_number,coalesce(w.nomor_urut,''),coalesce(q.name,''), \
                                       case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end, \
                                       c.sd_type,coalesce(b.est_delivery_date,a.max_est_delivery_date), \
                                       cast(coalesce(b.sequence_line_1_moved1,'0') as int), \
                                       coalesce(b.sequence_line,a.name),coalesce(d.partner_alias,d.name),a.date_order, \
                                       coalesce(v.kode_transaksi_faktur_pajak,'') || '.' || coalesce(w.name,''), \
                                       c.default_code,c.name_template,a.name,b.product_uom, \
                                       coalesce(z.name,''),coalesce(y.tax_name,''),coalesce(i.name,''), \
                                       case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end", 
                                  (data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['usage'],
                                    data['form']['goods_type'],
                                    data['form']['sale_type'],))
            elif data['form']['sale_type'] == 'local':
                self.cr.execute (s + " where u2.usage=%s and \
                                       a.goods_type = %s \
                                       and a.sale_type = %s \
                                       and a.locale_sale_type like %s \
                                       and v.currency_id = %s \
                                       group by coalesce(u.alias,u.name,''),g.name,to_char(g.date_done,'YYYY-MM-DD'), \
                                       to_char(g.date_done,'DD/MM/YYYY'),v.internal_number,coalesce(v.peb_number,''),coalesce(w.nomor_urut,''),coalesce(q.name,''), \
                                       case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end, \
                                       c.sd_type,coalesce(b.est_delivery_date,a.max_est_delivery_date), \
                                       cast(coalesce(b.sequence_line_1_moved1,'0') as int), \
                                       coalesce(b.sequence_line,a.name),coalesce(d.partner_code,''),coalesce(d.partner_alias,d.name),a.date_order, \
                                       track.tracking, \
                                       coalesce(v.kode_transaksi_faktur_pajak,'') || '.' || coalesce(w.name,''), \
                                       c.default_code,c.name_template,a.name,b.product_uom, \
                                       coalesce(z.name,''),coalesce(y.tax_name,''),coalesce(i.name,''), \
                                       case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end,f.name \
                                       order by coalesce(u.alias,u.name,''),g.name,to_char(g.date_done,'YYYY-MM-DD'), \
                                       v.internal_number,coalesce(w.nomor_urut,''),coalesce(q.name,''), \
                                       case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end, \
                                       c.sd_type,coalesce(b.est_delivery_date,a.max_est_delivery_date), \
                                       cast(coalesce(b.sequence_line_1_moved1,'0') as int), \
                                       coalesce(b.sequence_line,a.name),coalesce(d.partner_alias,d.name),a.date_order, \
                                       coalesce(v.kode_transaksi_faktur_pajak,'') || '.' || coalesce(w.name,''), \
                                       c.default_code,c.name_template,a.name,b.product_uom, \
                                       coalesce(z.name,''),coalesce(y.tax_name,''),coalesce(i.name,''), \
                                       case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end", 
                                  (data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['usage'],
                                    data['form']['goods_type'],
                                    data['form']['sale_type'],
                                    data['form']['locale_sale_type'],
                                    data['form']['currency_id'][0],))

        elif sheet == 'invoice':
            if data['form']['sale_type'] == 'export':
                self.cr.execute (s + " where u2.usage=%s and \
                                       a.goods_type = %s \
                                       and a.sale_type = %s \
                                       group by coalesce(u.alias,u.name,''),g.name,to_char(g.date_done,'YYYY-MM-DD'), \
                                       to_char(g.date_done,'DD/MM/YYYY'),v.internal_number,coalesce(v.peb_number,''),coalesce(w.nomor_urut,''),coalesce(q.name,''), \
                                       case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end, \
                                       c.sd_type,coalesce(b.est_delivery_date,a.max_est_delivery_date), \
                                       cast(coalesce(b.sequence_line_1_moved1,'0') as int), \
                                       coalesce(b.sequence_line,a.name),coalesce(d.partner_code,''),coalesce(d.partner_alias,d.name),a.date_order, \
                                       track.tracking, \
                                       coalesce(v.kode_transaksi_faktur_pajak,'') || '.' || coalesce(w.name,''), \
                                       c.default_code,c.name_template,a.name,b.product_uom, \
                                       coalesce(z.name,''),coalesce(y.tax_name,''),coalesce(i.name,''), \
                                       case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end,f.name \
                                       order by v.internal_number,coalesce(u.alias,u.name,''),g.name,to_char(g.date_done,'YYYY-MM-DD'), \
                                       coalesce(w.nomor_urut,''),coalesce(q.name,''), \
                                       case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end, \
                                       c.sd_type,coalesce(b.est_delivery_date,a.max_est_delivery_date), \
                                       cast(coalesce(b.sequence_line_1_moved1,'0') as int), \
                                       coalesce(b.sequence_line,a.name),coalesce(d.partner_alias,d.name),a.date_order, \
                                       coalesce(v.kode_transaksi_faktur_pajak,'') || '.' || coalesce(w.name,''), \
                                       c.default_code,c.name_template,a.name,b.product_uom, \
                                       coalesce(z.name,''),coalesce(y.tax_name,''),coalesce(i.name,''), \
                                       case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end", 
                                  (data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['usage'],
                                    data['form']['goods_type'],
                                    data['form']['sale_type'],))
            elif data['form']['sale_type'] == 'local':
                self.cr.execute (s + " where u2.usage=%s and \
                                       a.goods_type = %s \
                                       and a.sale_type = %s \
                                       and a.locale_sale_type like %s \
                                       and v.currency_id = %s \
                                       group by coalesce(u.alias,u.name,''),g.name,to_char(g.date_done,'YYYY-MM-DD'), \
                                       to_char(g.date_done,'DD/MM/YYYY'),v.internal_number,coalesce(v.peb_number,''),coalesce(w.nomor_urut,''),coalesce(q.name,''), \
                                       case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end, \
                                       c.sd_type,coalesce(b.est_delivery_date,a.max_est_delivery_date), \
                                       cast(coalesce(b.sequence_line_1_moved1,'0') as int), \
                                       coalesce(b.sequence_line,a.name),coalesce(d.partner_code,''),coalesce(d.partner_alias,d.name),a.date_order, \
                                       track.tracking, \
                                       coalesce(v.kode_transaksi_faktur_pajak,'') || '.' || coalesce(w.name,''), \
                                       c.default_code,c.name_template,a.name,b.product_uom, \
                                       coalesce(z.name,''),coalesce(y.tax_name,''),coalesce(i.name,''), \
                                       case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end,f.name \
                                       order by v.internal_number,coalesce(u.alias,u.name,''),g.name,to_char(g.date_done,'YYYY-MM-DD'), \
                                       coalesce(w.nomor_urut,''),coalesce(q.name,''), \
                                       case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end, \
                                       c.sd_type,coalesce(b.est_delivery_date,a.max_est_delivery_date), \
                                       cast(coalesce(b.sequence_line_1_moved1,'0') as int), \
                                       coalesce(b.sequence_line,a.name),coalesce(d.partner_alias,d.name),a.date_order, \
                                       coalesce(v.kode_transaksi_faktur_pajak,'') || '.' || coalesce(w.name,''), \
                                       c.default_code,c.name_template,a.name,b.product_uom, \
                                       coalesce(z.name,''),coalesce(y.tax_name,''),coalesce(i.name,''), \
                                       case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end", 
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
            if data['form']['sale_type'] == 'export':
                self.cr.execute (s + " where u2.usage=%s and \
                                       a.goods_type = %s \
                                       and a.sale_type = %s \
                                       group by case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end,coalesce(d.partner_code,''),coalesce(d.partner_alias,d.name),g.name,to_char(g.date_done,'YYYY-MM-DD'), \
                                       to_char(g.date_done,'DD/MM/YYYY'),v.internal_number,coalesce(v.peb_number,''),coalesce(w.nomor_urut,''),coalesce(q.name,''), \
                                       case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end, \
                                       c.sd_type,coalesce(b.est_delivery_date,a.max_est_delivery_date), \
                                       cast(coalesce(b.sequence_line_1_moved1,'0') as int), \
                                       coalesce(b.sequence_line,a.name),a.date_order, \
                                       track.tracking, \
                                       coalesce(v.kode_transaksi_faktur_pajak,'') || '.' || coalesce(w.name,''), \
                                       c.default_code,c.name_template,a.name,b.product_uom, \
                                       coalesce(z.name,''),coalesce(y.tax_name,''),coalesce(i.name,''), \
                                       coalesce(u.alias,u.name,'') ,f.name\
                                       order by case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end,coalesce(d.partner_alias,d.name),g.name,to_char(g.date_done,'YYYY-MM-DD'), \
                                       v.internal_number,coalesce(w.nomor_urut,''),coalesce(q.name,''), \
                                       case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end, \
                                       c.sd_type,coalesce(b.est_delivery_date,a.max_est_delivery_date), \
                                       cast(coalesce(b.sequence_line_1_moved1,'0') as int), \
                                       coalesce(b.sequence_line,a.name),a.date_order, \
                                       coalesce(v.kode_transaksi_faktur_pajak,'') || '.' || coalesce(w.name,''), \
                                       c.default_code,c.name_template,a.name,b.product_uom, \
                                       coalesce(z.name,''),coalesce(y.tax_name,''),coalesce(i.name,''), \
                                       coalesce(u.alias,u.name,'')", 
                                  (data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['date_from'], 
                                    data['form']['date_to'], 
                                    data['form']['usage'],
                                    data['form']['goods_type'],
                                    data['form']['sale_type'],))
            elif data['form']['sale_type'] == 'local':
                self.cr.execute (s + " where u2.usage=%s and \
                                       a.goods_type = %s \
                                       and a.sale_type = %s \
                                       and a.locale_sale_type like %s \
                                       and v.currency_id = %s \
                                       group by case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end,coalesce(d.partner_code,''),coalesce(d.partner_alias,d.name),g.name,to_char(g.date_done,'YYYY-MM-DD'), \
                                       to_char(g.date_done,'DD/MM/YYYY'),v.internal_number,coalesce(v.peb_number,''),coalesce(w.nomor_urut,''),coalesce(q.name,''), \
                                       case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end, \
                                       c.sd_type,coalesce(b.est_delivery_date,a.max_est_delivery_date), \
                                       cast(coalesce(b.sequence_line_1_moved1,'0') as int), \
                                       coalesce(b.sequence_line,a.name),a.date_order, \
                                       track.tracking, \
                                       coalesce(v.kode_transaksi_faktur_pajak,'') || '.' || coalesce(w.name,''), \
                                       c.default_code,c.name_template,a.name,b.product_uom, \
                                       coalesce(z.name,''),coalesce(y.tax_name,''),coalesce(i.name,''), \
                                       coalesce(u.alias,u.name,''),f.name \
                                       order by case when a.sale_type = 'local' then 'Indonesia' else coalesce(trc.name,'') end,coalesce(d.partner_alias,d.name),g.name,to_char(g.date_done,'YYYY-MM-DD'), \
                                       v.internal_number,coalesce(w.nomor_urut,''),coalesce(q.name,''), \
                                       case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end, \
                                       c.sd_type,coalesce(b.est_delivery_date,a.max_est_delivery_date), \
                                       cast(coalesce(b.sequence_line_1_moved1,'0') as int), \
                                       coalesce(b.sequence_line,a.name),a.date_order, \
                                       coalesce(v.kode_transaksi_faktur_pajak,'') || '.' || coalesce(w.name,''), \
                                       c.default_code,c.name_template,a.name,b.product_uom, \
                                       coalesce(z.name,''),coalesce(y.tax_name,''),coalesce(i.name,''), \
                                       coalesce(u.alias,u.name,'')", 
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

# report_sxw.report_sxw('report.sales.report',
#                         'report.sales.wizard', 
#                         '', parser=ReportSalesOrder)
# report_sxw.report_sxw('report.penjualan.form', 'report.keuangan', 'addons/ad_laporan_keuangan/report/salesreport.mako', parser=ReportKeu)