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

class booked_order_sales_parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(booked_order_sales_parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_date_from': self._get_date_from,
            'get_date_to': self._get_date_to,
            'get_view': self._get_view,
            'xdate': self._xdate,
            'get_title': self._get_title,            
            'uom_to_bales': self._uom_to_bales,            
            'uom_to_base': self._uom_to_base,            
            'price_per_bales': self._price_per_bales,
            'price_per_base': self._price_per_base,            
            'get_company': self._get_company, 
            'get_uom_base': self._get_uom_base,           
            'get_price_base': self._get_price_base, 
            'get_print_user_time': self._get_print_user_time,          
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

    def _get_date_from(self,data,context=None):
        return datetime.strptime(data['form']['date_from'],'%Y-%m-%d').strftime('%d/%m/%Y')
    
    def _get_date_to(self,data,context=None):
        return datetime.strptime(data['form']['date_to'],'%Y-%m-%d').strftime('%d/%m/%Y')
    
    def _get_title(self,sheet):
        if sheet == 'customer':
            return 'BOOKED ORDER - CUSTOMER WISE'
        elif sheet == 'product':
            return 'BOOKED ORDER - PRODUCT WISE'
        elif sheet == 'date':
            return 'BOOKED ORDER - DATE WISE'

    def _get_uom_base(self,data):
        if data['form']['sale_type'] == 'export':
          uom_base = 'BALES'
        elif data['form']['sale_type'] == 'local':
          uom_base = 'BALES'
        else:
          uom_base = 'KGS'
        return uom_base

    def _get_price_base(self,data):
        if data['form']['sale_type'] == 'export':
          price_base = 'US$/KG'
        elif data['form']['sale_type'] == 'local':
          price_base = 'US$/BALE'
        else:
          price_base = 'US$/KG'
        return price_base

    def _uom_to_bales(self,qty,uom_source):
        cr = self.cr
        uid = self.uid
        bale = self.pool.get('product.uom').search(cr,uid,[('name','=','BALES')])
        qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, qty, to_uom_id=bale and bale[0] or False)
        return qty_result

    def _uom_to_base(self,data,qty,uom_source):
        cr = self.cr
        uid = self.uid
        if data['form']['sale_type'] == 'export':
          uom_base = 'BALES'
        elif data['form']['sale_type'] == 'local':
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

    def _price_per_base(self,data,price,uom_source):
        cr = self.cr
        uid = self.uid
        if data['form']['sale_type'] == 'export':
          uom_base = 'KGS'
        elif data['form']['sale_type'] == 'local':
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

    def _get_company(self,context=None):
        self.cr.execute ("select upper(b.name) as name \
                          from res_company a \
                          left join res_partner b on a.partner_id = b.id")

        res = self.cr.fetchone()
        return res

    def _get_view(self,data,sheet,context=None):
        s = "select coalesce(u.alias,u.name,'') as loc_name, \
            c.default_code as product_name, \
            c.name_template as product_descr, \
            coalesce(b.sequence_line,a.name) as name, a.date_order, \
            coalesce(d.partner_alias,d.name) as customer_name, \
            coalesce(b.est_delivery_date,a.max_est_delivery_date) as sale_order_lsd, \
            (case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then null else af.date_expected end) as sale_order_scd, \
            (case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end) as sale_order_scd_sort, \
            coalesce(e.alias,'') as packing_name, \
            b.cone_weight,b.product_uom_qty, \
            b.product_uom, \
            coalesce(f.name,'') as uom_name, \
            b.product_uom_qty as bal_qty, \
            (b.product_uom_qty+coalesce(g.product_qty,0.0)) as bal_qty1, \
            b.price_unit, \
            b.product_uom_qty * b.price_unit as bal_amount, \
            (b.product_uom_qty+coalesce(g.product_qty,0.0)) * b.price_unit as bal_amount1, \
            coalesce(h.commission_percentage,0.0) as commission_percentage, \
            (case when coalesce(h.comm_count,0)>1 then '*' else '' end) as comm_star, \
            coalesce(i.name,'') as payment_term_name, \
            coalesce(k.name,'') as book_by,a.note, \
            coalesce(m.alias,m.name,'') as container_size_name, \
            '' as pay_status, \
            p.lc_recvd_date, \
            p.lc_lsd, \
            coalesce(q.name,'') as blend, \
            c.count as count_id, \
            coalesce(r2.name,coalesce(r.name,'')) as destination, \
            coalesce(b.remarks,'') as remarks, \
            coalesce(q.name,'') || '/' || case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end as blend_count, \
            coalesce(s.code,'') as incoterm, \
            c.sd_type \
            from sale_order a \
            inner join sale_order_line b on a.id = b.order_id \
            inner join product_product c on b.product_id = c.id \
            inner join res_partner d on a.partner_shipping_id = d.id \
            left join packing_type e on b.packing_type = e.id \
            left join product_uom f on b.product_uom = f.id \
            left join (select g1.sale_id, g2.product_id, g2.sequence_line, g2.sale_line_id, \
                              sum(case g1.type \
                                  when 'in' then g2.product_qty \
                                  when 'out' then -g2.product_qty \
                                  else 0 end) as product_qty \
                       from stock_picking g1 \
                       inner join stock_move g2 on g1.id=g2.picking_id \
                       where g1.state='done' and to_char(g1.date_done,'YYYY-MM-DD') <= substring(%s,1,10) \
                            and coalesce(g1.sale_id,0) <> 0 and coalesce(g2.sale_line_id,0) <> 0 \
                       group by g1.sale_id,g2.product_id,g2.sequence_line,g2.sale_line_id) g \
                  on a.id = g.sale_id and b.product_id = g.product_id and b.id = g.sale_line_id \
            left join (select sale_id,sale_line_id,sum(commission_percentage) as commission_percentage, \
                       count(sale_id) as comm_count \
                       from sale_order_agent \
                       group by sale_id,id) h on a.id = h.sale_id and h.sale_line_id=b.id \
            left join account_payment_term i on a.payment_term = i.id \
            left join res_users j on a.user_id = j.id \
            left join res_partner k on j.partner_id = k.id \
            left join container_size m on b.container_size = m.id \
            left join (select n.lc_id as order_id,o1.id,o2.product_id,o2.sequence_line,o2.sale_line_id, \
                       o1.rcvd_smg as lc_recvd_date, \
                       coalesce(o2.est_delivery_date,o1.lc_ship_valid_date) as lc_lsd \
                       from sale_order_letterofcredit_rel n \
                       inner join letterofcredit o1 on n.order_id = o1.id \
                       inner join letterofcredit_product_line o2 on o1.id = o2.lc_id \
                       where o1.state not in ('nonactive')) p on b.order_id = p.order_id and b.product_id = p.product_id and b.id = p.sale_line_id \
            left join mrp_blend_code q on c.blend_code = q.id \
            left join res_country r on a.dest_country_id = r.id \
            left join res_port r2 on a.dest_port_id = r2.id \
            left join stock_incoterms s on a.incoterm = s.id \
            left join (select * from ir_property where name='property_stock_production') t on trim(t.res_id) = 'product.template,' || trim(cast(c.product_tmpl_id as text)) \
            left join (select * from stock_location where usage='production') u on 'stock.location,' || (cast(u.id as text)) = trim(t.value_reference) \
            left join (select af1.sale_id, af2.product_id, af2.sequence_line, af2.sale_line_id, max(af2.date_expected) as date_expected, \
                              sum(case af1.type \
                                  when 'in' then af2.product_qty \
                                  when 'out' then -af2.product_qty \
                                  else 0 end) as product_qty \
                       from stock_picking af1 \
                       inner join stock_move af2 on af1.id=af2.picking_id \
                       where af1.state not in ('done','cancel') and af2.state not in ('done','cancel') \
                            and coalesce(af1.sale_id,0) <> 0 and coalesce(af2.sale_line_id,0) <> 0 \
                       group by af1.sale_id,af2.product_id,af2.sequence_line,af2.sale_line_id) af \
                  on a.id = af.sale_id and b.product_id = af.product_id and b.id = af.sale_line_id \
            where a.state not in ('draft','cancel') \
            and to_char(a.date_order,'YYYY-MM-DD') <= substring(%s,1,10) \
            and a.goods_type = %s \
            and a.sale_type = %s \
            and to_char(a.date_order,'YYYY-MM-DD') >= substring(%s,1,10)"

        spartner = '' 
        if data['form']['filter'] == 'filter_cust':
            for pid in data['form']['partner_id']:
                if spartner == '':
                    spartner = str(pid)
                else:
                    spartner += ','+str(pid)
        
        if spartner == '':
            spartner = '0'
        spartner = '('+spartner+')' 

        if sheet == 'customer':
            sorder =    "order by coalesce(u.alias,u.name,''),coalesce(q.name,''), \
                        case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end,c.sd_type, \
                        coalesce(d.partner_alias,d.name), \
                        case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then \
                        coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end, \
                        to_char(a.date_order,'YYYY-MM-DD'), \
                        cast(coalesce(b.sequence_line_1_moved1,'0') as int),coalesce(b.sequence_line,a.name)" 
        elif sheet == 'product':
            sorder =    "order by coalesce(u.alias,u.name,''),coalesce(q.name,''), \
                        case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end,c.sd_type, \
                        case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then \
                        to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') else to_char(coalesce(af.date_expected,b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') end, \
                        to_char(a.date_order,'YYYY-MM-DD'), \
                        cast(coalesce(b.sequence_line_1_moved1,'0') as int),coalesce(b.sequence_line,a.name), \
                        coalesce(d.partner_alias,d.name)"
        elif sheet == 'date':
            sorder =    "order by coalesce(u.alias,u.name,''),to_char(a.date_order,'YYYY-MM-DD'), \
                        cast(coalesce(b.sequence_line_1_moved1,'0') as int),coalesce(b.sequence_line,a.name), \
                        coalesce(d.partner_alias,d.name),coalesce(q.name,''), \
                        case when coalesce(c.count,0.0)>0 then cast(c.count as text) else '' end,c.sd_type, \
                        case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then \
                        coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end"

        if data['form']['sale_type'] == 'export':
            if data['form']['filter'] == 'filter_cust':
                s += " and a.partner_id in "+spartner 
            s += " " + sorder 
            self.cr.execute (s, 
                            (data['form']['date_to'],
                            data['form']['date_to'], 
                            data['form']['goods_type'],
                            data['form']['sale_type'],
                            data['form']['date_from'],))
        elif data['form']['sale_type'] == 'local':
            s += " and a.locale_sale_type like %s" 
            if data['form']['filter'] == 'filter_cust':
                s += " and a.partner_id in "+spartner 
            s += " " + sorder 
            self.cr.execute (s, 
                            (data['form']['date_to'], 
                            data['form']['date_to'],
                            data['form']['goods_type'],
                            data['form']['sale_type'],
                            data['form']['date_from'],
                            data['form']['locale_sale_type'],))

        res = self.cr.dictfetchall()
        return res

report_sxw.report_sxw('report.booked.order.sales.report', 'report.booked.order.sales.wizard', 'addons/ad_sales_report/report/booked_order_sales_report.mako', parser=booked_order_sales_parser,header=False) 
