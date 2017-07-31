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

class production_planning_parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(production_planning_parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_object' : self._get_object,
            'get_goods_type': self._get_goods_type,
            'get_as_on': self._get_as_on,
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

    def _get_title(self,sheet):
        if sheet == 'customer':
            return 'PRODUCTION PLANNING - CUSTOMER WISE'
        elif sheet == 'product':
            return 'PRODUCTION PLANNING - PRODUCT WISE'
        elif sheet == 'contract':
            return 'PRODUCTION PLANNING - CONTRACT WISE'

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
        
    def _get_as_on(self,data,context=None):
        return datetime.strptime(data['form']['as_on'],'%Y-%m-%d').strftime('%d/%m/%Y')
    
    def _get_data_so(self,data,context=None):
        sale_obj    = self.pool.get('sale.order')
        sale_ids    = False
#        if data['form']['sale_type'] == 'export':
#            sale_ids        = sale_obj.search(self.cr, self.uid, [('state','not in',('draft','cancel')),
#                                                        ('goods_type','=',data['form']['goods_type']),
#                                                        ('sale_type','=',data['form']['sale_type']),
#                                                        ('date_order','<=',data['form']['as_on'])])
#        elif data['form']['sale_type'] == 'local':
#            sale_ids        = sale_obj.search(self.cr, self.uid, [('state','not in',('draft','cancel')),
#                                                        ('goods_type','=',data['form']['goods_type']),
#                                                        ('sale_type','=',data['form']['sale_type']),
#                                                        ('locale_sale_type','=',data['form']['locale_sale_type']),
#                                                        ('date_order','<=',data['form']['as_on'])])

        sale_ids = sale_obj.search(self.cr, self.uid, [('state','not in',('draft','cancel'))])
        if sale_ids:
            sale_data = sale_obj.browse(self.cr, self.uid,sale_ids)
            return sale_data
        else:
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
        sale_obj    = self.pool.get('sale.order')
        pick_obj    = self.pool.get('stock.picking')
        move_obj    = self.pool.get('stock.move')
        sale_ids    = False
        if data['form']['sale_type'] == 'export':
            sale_ids        = sale_obj.search(self.cr, self.uid, [('state','not in',('draft','cancel')),
                                                        ('goods_type','=',data['form']['goods_type']),
                                                        ('sale_type','=',data['form']['sale_type']),
                                                        ('date_order','<=',data['form']['as_on'])])
        elif data['form']['sale_type'] == 'local':
            sale_ids        = sale_obj.search(self.cr, self.uid, [('state','not in',('draft','cancel')),
                                                        ('goods_type','=',data['form']['goods_type']),
                                                        ('sale_type','=',data['form']['sale_type']),
                                                        ('locale_sale_type','=',data['form']['locale_sale_type']),
                                                        ('date_order','<=',data['form']['as_on'])])
        if sale_ids:
            picking_ids = pick_obj.search(self.cr,self.uid,[('sale_id','in',sale_ids)])
            if picking_ids:
                move_ids = move_obj.search(self.cr,self.uid,[('picking_id','in',picking_ids)],order="location_id asc,product_id asc")
                return move_obj.browse(self.cr,self.uid,move_ids)
        return False

    def _get_company(self,context=None):
        self.cr.execute ("select upper(b.name) as name \
                          from res_company a \
                          left join res_partner b on a.partner_id = b.id")

        res = self.cr.fetchone()
        return res

    def _get_view(self,data,sheet,context=None):
        s = "select \
                coalesce(slprod2.alias,slprod2.name,'') as loc_name, \
                pp.default_code as product_name, \
                pp.name_template as product_descr, \
                coalesce(sol.sequence_line,so.name) as name, \
                so.name as sale_order_name, \
                so.date_order, \
                coalesce(rp.partner_alias,rp.name) as customer_name, \
                coalesce(sol.est_delivery_date,so.max_est_delivery_date) as sale_order_lsd, \
                to_char(coalesce(sol.est_delivery_date,so.max_est_delivery_date),'MM-YYYY') as sale_order_lsp, \
                case when coalesce(sol.est_delivery_date::date,so.max_est_delivery_date::date)=dump_lc.schd_date then null \
                    else dump_lc.schd_date end as sale_order_scd, \
                case when coalesce(sol.est_delivery_date::date,so.max_est_delivery_date::date)=dump_lc.schd_date then coalesce(sol.est_delivery_date::date, \
                    so.max_est_delivery_date::date) \
                    else dump_lc.schd_date end as sale_order_scd_sort, \
                coalesce(packt.alias,packt.name) as packing_name, \
                sol.cone_weight,sol.product_uom_qty, sol.product_uom, \
                coalesce(pusol.name,'') as uom_name, \
                (sol.product_uom_qty-coalesce(dump_lc.total_shipped_lc_as_on,dum_smm.shipped_qty,0.0)) as bal_qty, \
                coalesce(dump_lc.shipped_lc_qty,dum_smm.shipped_qty,0.0) as shipped_qty, \
                sol.price_unit, \
                dump_lc.lc_qty, \
                (sol.product_uom_qty-coalesce(dump_lc.total_shipped_lc_as_on,dum_smm.shipped_qty,0.0))*sol.price_unit as bal_amount, \
                coalesce(scomm.commission_percentage,0.0) as commission_percentage, \
                (case when coalesce(scomm.comm_count,0)>1 then '*' else '' end) as comm_star, \
                coalesce(apt.alias,apt.name,'') as payment_term_name, \
                coalesce(rusp.name,'') as book_by,so.note, \
                coalesce(cs.alias,cs.name,'') as container_size_name, \
                ''::text as pay_status, \
                lch.rcvd_smg as lc_recvd_date, \
                coalesce(lcpl.est_delivery_date,lch.lc_ship_valid_date) as lc_lsd , \
                coalesce(mbc.name,'') as blend, \
                pp.count as count_id, \
                coalesce(port.name,coalesce(r.name,'')) as destination, \
                coalesce(sol.remarks,'') as remarks, \
                coalesce(mbc.name,'') || '/' || (case when coalesce(pp.count,0.0)>0 then cast(pp.count as text) else '-' end) as blend_count, \
                coalesce(mbc.name,'') || '/' || (case when coalesce(pp.count,0.0)>0 then cast(pp.count as text) else '-' end) || '/' || (case when coalesce(pp.sd_type,'')!='' then pp.sd_type else '-' end) as blend_count_sd, \
                coalesce(s.code,'') as incoterm, \
                pp.sd_type, \
                upper(left(sol.order_state,1)) as order_state \
                from sale_order_line sol \
                left join (select sale_line_id,sum(commission_percentage) as commission_percentage, \
                    count(sale_id) as comm_count \
                    from sale_order_agent \
                    group by sale_line_id) scomm on sol.id = scomm.sale_line_id \
                left join product_uom pusol on pusol.id=sol.product_uom \
                left join product_product pp on sol.product_id=pp.id \
                left join product_template pt on pp.product_tmpl_id=pt.id \
                inner join sale_order so on sol.order_id=so.id \
                left join account_payment_term apt on so.payment_term = apt.id \
                inner join res_partner rp on so.partner_shipping_id=rp.id \
                left join packing_type packt on sol.packing_type = packt.id \
                left join container_size cs on sol.container_size = cs.id \
                left join res_users rus on so.user_id=rus.id \
                left join res_partner rusp on rus.partner_id=rusp.id \
                left join (select * from ir_property where name='property_stock_production') ip \
                    on trim(ip.res_id) = 'product.template,' || trim(cast(pp.product_tmpl_id as text)) \
                left join (select id,name,alias from stock_location where usage='production') slprod \
                    on 'stock.location,' || (cast(slprod.id as text)) = trim(ip.value_reference) \
                left join (select id,name,alias from stock_location where usage='production') slprod2 \
                    on slprod2.id = sol.production_location \
                left join ( \
                        select dum1.*,dum2.total_shipped_lc_as_on,rank() OVER (PARTITION BY dum1.sol_id ORDER BY dum1.lc_prod_line_id DESC) \
                        from lc_shipment_sol(%s::timestamp,%s,%s) dum1 \
                        left join \
                            ( \
                            select xr.sol_id,min(xr.lc_lsd) as min_dt,sum(xr.shipped_lc_qty) as total_shipped_lc_as_on \
                            from lc_shipment_sol(%s::timestamp,%s,%s) xr group by xr.sol_id,xr.prod_id \
                            ) dum2 \
                            on \
                            dum2.sol_id=dum1.sol_id \
                            and dum1.lc_lsd=dum2.min_dt \
                    ) dump_lc on dump_lc.sol_id=sol.id and dump_lc.rank=1 \
                left join letterofcredit_product_line lcpl on lcpl.id=dump_lc.lc_prod_line_id \
                left join letterofcredit lch on lch.id = lcpl.lc_id \
                left join mrp_blend_code mbc on pp.blend_code = mbc.id \
                left join res_port port on so.dest_port_id = port.id \
                left join res_country r on so.dest_country_id = r.id \
                left join stock_incoterms s on so.incoterm = s.id \
                left join ( \
                    select \
                        smm.sale_line_id,smm.product_id, \
                        case when spm.type='out' then \
                            sum(round((coalesce(smm.product_qty,0.0)/pum2.factor)*pum1.factor,4)) \
                        else \
                            sum(round((coalesce(-1*smm.product_qty,0.0)/pum2.factor)*pum1.factor,4)) \
                        end as shipped_qty \
                    from stock_move smm \
                        left join sale_order_line solm on smm.sale_line_id=solm.id \
                        inner join stock_picking spm on smm.picking_id=spm.id \
                        inner join stock_location slm1 on smm.location_id=slm1.id \
                        inner join stock_location slm2 on smm.location_dest_id=slm2.id \
                        inner join product_uom pum1 on solm.product_uom=pum1.id \
                        inner join product_uom pum2 on smm.product_uom=pum2.id \
                    where \
                        smm.date::date<=%s::date and smm.state='done' \
                        and ((slm1.usage='internal' and slm2.usage='customer') or (slm1.usage='customer' and slm2.usage='internal')) \
                        and spm.goods_type=%s and spm.sale_type=%s \
                    group by smm.sale_line_id,smm.product_id,spm.type \
                    ) dum_smm on sol.id=dum_smm.sale_line_id and sol.product_id=dum_smm.product_id \
                 \
                where \
                so.state not in ('draft','cancel') and so.date_order::date <= %s\
                and to_char(so.date_order,'YYYY-MM-DD') <= substring(%s,1,10) \
                and ((so.date_done is null) or (to_char(so.date_done,'YYYY-MM-DD') > substring(%s,1,10))) \
                and ((so.date_cancel is null) or (to_char(so.date_cancel,'YYYY-MM-DD') > substring(%s,1,10))) \
                and ((sol.date_knock_off is null or sol.knock_off=false) or (to_char(sol.date_knock_off,'YYYY-MM-DD') > substring(%s,1,10))) \
                and so.goods_type = %s \
                and so.sale_type=%s "
        
        if sheet == 'customer':
            sorder =    " order by coalesce(slprod2.alias,slprod2.name,''),coalesce(mbc.name,''), \
                        case when coalesce(mbc.count,0.0)>0 then cast(mbc.count as text) else '' end,mbc.sd_type, \
                        coalesce(rp.partner_alias,rp.name), \
                        case when coalesce(sol.est_delivery_date::date,so.max_est_delivery_date::date)!=dump_lc.schd_date then dump_lc.schd_date end, \
                        coalesce(sol.est_delivery_date,so.max_est_delivery_date), \
                        to_char(so.date_order,'YYYY-MM-DD'), \
                        cast(coalesce(sol.sequence_line_1,'0') as int),coalesce(sol.sequence_line,so.name) " 
        elif sheet == 'product':
            sorder =    " order by coalesce(slprod2.alias,slprod2.name,''),coalesce(mbc.name,''),  \
                        case when coalesce(pp.count,0.0)>0 then cast(pp.count as text) else '' end,pp.sd_type, \
                        case when coalesce(sol.est_delivery_date::date,so.max_est_delivery_date::date)!=dump_lc.schd_date then dump_lc.schd_date end, \
                        coalesce(sol.est_delivery_date,so.max_est_delivery_date),  \
                        to_char(so.date_order,'YYYY-MM-DD'),  \
                        cast(coalesce(sol.sequence_line_1,'0') as int),coalesce(sol.sequence_line,so.name), \
                        coalesce(rp.partner_alias,rp.name) "
        elif sheet == 'contract':
            sorder =    " order by coalesce(slprod2.alias,slprod2.name,''),to_char(so.date_order,'YYYY-MM-DD'), \
                        cast(coalesce(sol.sequence_line_1,'0') as int),coalesce(sol.sequence_line,so.name), \
                        coalesce(mbc.name,''), \
                        case when coalesce(pp.count,0.0)>0 then cast(pp.count as text) else '' end,pp.sd_type, \
                        case when coalesce(sol.est_delivery_date::date,so.max_est_delivery_date::date)!=dump_lc.schd_date then dump_lc.schd_date end, \
                        coalesce(sol.est_delivery_date,so.max_est_delivery_date),coalesce(rp.partner_alias,rp.name) "

        if data['form']['sale_type'] == 'export':
            s += " " + sorder 
            self.cr.execute (s, 
                            (
                            data['form']['as_on'],
                            data['form']['goods_type'],
                            data['form']['sale_type'],
                            data['form']['as_on'],
                            data['form']['goods_type'],
                            data['form']['sale_type'],
                            data['form']['as_on'],
                            data['form']['goods_type'],
                            data['form']['sale_type'],
                            data['form']['as_on'],
                            data['form']['as_on'],
                            data['form']['as_on'],
                            data['form']['as_on'],
                            data['form']['as_on'],
                            data['form']['goods_type'],
                            data['form']['sale_type'],
                            ))
        elif data['form']['sale_type'] == 'local':
            s += " and so.locale_sale_type like %s" 
            s += " " + sorder 
            self.cr.execute (s, 
                            (
                            data['form']['as_on'],
                            data['form']['goods_type'],
                            data['form']['sale_type'],
                            data['form']['as_on'],
                            data['form']['goods_type'],
                            data['form']['sale_type'],
                            data['form']['as_on'],
                            data['form']['goods_type'],
                            data['form']['sale_type'],
                            data['form']['as_on'],
                            data['form']['as_on'],
                            data['form']['as_on'],
                            data['form']['as_on'],
                            data['form']['as_on'],
                            data['form']['goods_type'],
                            data['form']['sale_type'],
                            data['form']['locale_sale_type'],))
        
        res = self.cr.dictfetchall()
        return res

report_sxw.report_sxw('report.production.planning.report', 'report.production.planning.wizard', 'addons/ad_sales_report/report/production_planning_report.mako', parser=production_planning_parser,header=False) 
