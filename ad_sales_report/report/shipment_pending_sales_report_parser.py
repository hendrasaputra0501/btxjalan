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
import cStringIO
import xlwt
from dateutil import tz
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from ad_account_optimization.report.report_engine_xls import report_xls


class shipment_pending_sales_parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(shipment_pending_sales_parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_object' : self._get_object,
            'get_date_from': self._get_date_from,
            'get_date_to': self._get_date_to,
            'get_view': self._get_view,
            'xdate': self._xdate,
            'get_title': self._get_title,            
            'get_company': self._get_company,
            'get_uom_base': self._get_uom_base,           
            'get_print_user_time': self._get_print_user_time,          
        })
        # print "mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm"
        
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

    def _get_title(self,data):
        s = 'SHIPMENTS & PENDING ORDERS'
        if data['form']['sale_type'] == 'export':
            s = 'EXPORT ' + s
        elif data['form']['sale_type'] == 'local':
            s = 'LOCAL ' + s
        return s

    def _get_uom_base(self,data):
        if data['form']['sale_type'] == 'export':
          uom_base = 'BALES'
        elif data['form']['sale_type'] == 'local':
          uom_base = 'BALES'
        else:
          uom_base = 'KGS'
        return uom_base

    def _get_object(self,data):
        obj_data=self.pool.get(data['model']).browse(self.cr,self.uid,[data['form']['id']])
        return obj_data
    
    def _get_date_from(self,data,context=None):
        return datetime.strptime(data['form']['date_from'],'%Y-%m-%d').strftime('%d/%m/%Y')

    def _get_date_to(self,data,context=None):
        return datetime.strptime(data['form']['date_to'],'%Y-%m-%d').strftime('%d/%m/%Y')
    
    def _get_company(self,context=None):
        self.cr.execute ("select upper(b.name) as name \
                          from res_company a \
                          left join res_partner b on a.partner_id = b.id \
                          where a.id = 1")

        res = self.cr.fetchone()
        return res

    def _get_view(self,data,context=None):
        s1 = "select \
            pu_b.name,pu_b.factor, \
            coalesce(rp_ai.name,rp_so.name) as cust_name, \
            1 as report_group, \
            coalesce(ap.name,'') as curr_name, \
            coalesce(b.sequence_line,a.name) as sc_no, \
            to_char(a.date_order,'DD/MM/YYYY') as sc_date, \
            c.default_code as prod_code, \
            c.name_template as prod_name, \
            coalesce(r2.destination,'') as destination, \
            b.price_unit, \
                  case when pu_b.name='KGS' \
                  then coalesce(b.price_unit,0.0)\
                  when pu_b.name='BALES' \
                  then coalesce(coalesce(b.price_unit,0.0)*181.44000,0.0) \
                  when pu_b.name='LBS' \
                  then coalesce(coalesce(b.price_unit,0.0)*2.20462262185,0.0) \
                  else 0 \
                  end as uom_base_price_unit, \
            coalesce(s2.code,s.code,'') as lc_terms, \
            coalesce(p.lc_number,'') as lc_no, \
            b.product_uom, \
            (case when a.sale_type = 'local' then 'BALES' else 'KGS' end) as uom_base, \
            sum(-coalesce(g.product_qty,0.0)) as uom_qty, \
                  case when pu_b.name='KGS' \
                  then sum(-coalesce(coalesce(g.product_qty,0.0)/181.44000,0.0)) \
                  when pu_b.name='BALES' \
                  then sum(-coalesce(g.product_qty,0.0)) \
                  when pu_b.name='LBS' \
                  then sum(-coalesce(coalesce(g.product_qty,0.0)/400,0.0)) \
                  else 0 \
                  end as uom_base_qty, \
                  \
            sum(-coalesce(g.product_qty,0.0) * b.price_unit) as amount, \
            to_char(g.date_done,'Mon-YYYY') as delivery, \
            to_char(g.date_done,'YYYYMM') as delivery_sort, \
            v.internal_number as invc_no, \
            to_char(v.date_invoice,'DD/MM/YYYY') as invc_dt, \
            coalesce(g.container_number,'') as container, \
            coalesce(v.bl_number,'') as bl_no, \
            (case when coalesce(v.bl_number,'')='' then to_char(g.estimation_deliv_date,'DD/MM/YYYY') else to_char(v.bl_date,'DD/MM/YYYY') end) as bl_dt, \
            to_char(g.estimation_arriv_date,'DD/MM/YYYY') as eta, \
            string_agg(coalesce(ae.name,''),',') as lot_no, \
            coalesce(b.tpi,'') as tpi \
            , soap.display_name as agent \
            ,soap.id as agent_id\
            from (  select g1.name,g1.date_done,g1.invoice_id,g1.container_number, \
                        g1.estimation_arriv_date,g1.estimation_deliv_date,g2.sequence_line,g2.sale_line_id, \
                        g2.location_id,g2.location_dest_id,g2.product_id,g2.tracking_id,g2.invoice_line_id, \
                        sum(case g1.type \
                          when 'in' then g2.product_qty \
                          when 'out' then -g2.product_qty \
                          else 0 end) as product_qty \
                        ,g1.destination_country\
                        ,g1.forwading_charge\
                    from stock_picking g1 \
                    inner join stock_move g2 on g1.id=g2.picking_id \
                    where g1.state='done' and g2.state='done' \
                        and (to_char(g1.date_done,'YYYY-MM-DD') between substring(%s,1,10) and substring(%s,1,10)) \
                        and coalesce(g1.sale_id,0) <> 0 and coalesce(g2.sale_line_id,0) <> 0 \
                    group by g1.name,g1.date_done,g1.invoice_id,g1.container_number, \
                        g1.estimation_arriv_date,g1.estimation_deliv_date,g2.sequence_line,g2.sale_line_id, \
                        g2.location_id,g2.location_dest_id,g2.product_id,g2.tracking_id,g2.invoice_line_id \
                        ,g1.destination_country,g1.forwading_charge) g \
            inner join sale_order_line b on g.product_id = b.product_id and g.sale_line_id = b.id \
            inner join sale_order a on b.order_id = a.id \
            inner join product_product c on g.product_id = c.id \
            inner join res_partner d on a.partner_shipping_id = d.id \
            left join product_uom f on b.product_uom = f.id \
            left join (select n.lc_id as order_id,o1.id,o1.lc_number,o1.lc_incoterm, \
                       o2.product_id,o2.sequence_line,o2.sale_line_id, \
                       o1.rcvd_smg as lc_recvd_date, \
                       coalesce(o2.est_delivery_date,o1.lc_ship_valid_date) as lc_lsd \
                       from sale_order_letterofcredit_rel n \
                       inner join letterofcredit o1 on n.order_id = o1.id \
                       inner join letterofcredit_product_line o2 on o1.id = o2.lc_id \
                       where o1.state not in ('nonactive')) p on b.order_id = p.order_id and b.product_id = p.product_id and b.id = p.sale_line_id \
            left join res_country r on a.dest_country_id = r.id \
            left join (select stc.id,stc.port_id,rpt.name as destination from stock_transporter_charge stc \
                left outer join res_port rpt on stc.port_id=rpt.id) r2 on g.forwading_charge = r2.id \
            left join stock_incoterms s on a.incoterm = s.id \
            left join stock_incoterms s2 on p.lc_incoterm = s2.id \
            left join account_invoice v on g.invoice_id = v.id \
            left join stock_tracking ae on g.tracking_id = ae.id \
            left join product_pricelist ao on a.pricelist_id = ao.id \
            left join res_currency ap on ao.currency_id = ap.id \
            \
            left join res_partner rp_ai on v.partner_id=rp_ai.id \
            left join res_partner rp_so on a.partner_id=rp_so.id \
            LEFT JOIN product_template pt on c.product_tmpl_id = pt.id \
            LEFT JOIN product_uom pu_b on b.product_uom = pu_b.id \
            LEFT JOIN product_uom pu_pt on pt.uom_id = pu_pt.id \
            \
                left join ( \
                          select rp.display_name,soa.sale_line_id,rp.id from sale_order_agent soa \
                            left join res_partner rp on soa.agent_id=rp.id ) soap on b.id=soap.sale_line_id \
            where a.goods_type = lower(%s) \
                and a.sale_type = %s \
                \
                "

        s2 = "select \
            pu_b.name,pu_b.factor, \
            coalesce(rp_so.name,rp_so.partner_alias) as cust_name, \
            2 as report_group, \
            coalesce(ap.name,'') as curr_name, \
            coalesce(b.sequence_line,a.name) as sc_no, \
            to_char(a.date_order,'DD/MM/YYYY') as sc_date, \
            c.default_code as prod_code, \
            c.name_template as prod_name, \
            coalesce(r2.name,'') as destination, \
            b.price_unit, \
                    case when pu_b.name='KGS' \
                    then coalesce(b.price_unit,0.0) \
                    when pu_b.name='BALES' \
                    then coalesce(coalesce(b.price_unit,0.0)/181.44000,0.0) \
                    when pu_b.name='LBS' \
                    then coalesce(coalesce(b.price_unit,0.0)*2.20462262185,0.0) \
                    else 0 \
                    end as uom_base_price_unit, \
            coalesce(s2.code,s.code,'') as lc_terms, \
            coalesce(p.lc_number,'') as lc_no, \
            b.product_uom, \
            (case when a.sale_type = 'local' then 'BALES' else 'KGS' end) as uom_base, \
            sum((b.product_uom_qty+coalesce(g.product_qty,0.0))) as uom_qty, \
            \
                  case when pu_b.name='KGS' \
                  then sum(coalesce((b.product_uom_qty+coalesce(g.product_qty,0.0))/181.44000,0.0)) \
                  when pu_b.name='BALES' \
                  then sum((b.product_uom_qty+coalesce(g.product_qty,0.0))) \
                  when pu_b.name='LBS' \
                  then sum(coalesce((b.product_uom_qty+coalesce(g.product_qty,0.0))/400,0.0)) \
                  else 0 \
                  end as uom_base_qty, \
            \
            sum((b.product_uom_qty+coalesce(g.product_qty,0.0)) * b.price_unit) as amount, \
            to_char((case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end),'Mon-YYYY') as delivery, \
            to_char((case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end),'YYYYMM') as delivery_sort, \
            '' as invc_no, \
            '' as invc_dt, \
            '' as container, \
            '' as bl_no, \
            '' as bl_dt, \
            '' as eta, \
            string_agg('',',') as lot_no, \
            '' as tpi \
            , soap.display_name as agent \
            ,soap.id as agent_id \
            from sale_order a \
            inner join sale_order_line b on a.id = b.order_id \
            inner join product_product c on b.product_id = c.id \
            inner join res_partner d on a.partner_shipping_id = d.id \
            left join product_uom f on b.product_uom = f.id \
            left join (select g2.product_id, g2.sequence_line, g2.sale_line_id, \
                              sum(case g1.type \
                                  when 'in' then g2.product_qty \
                                  when 'out' then -g2.product_qty \
                                  else 0 end) as product_qty \
                                  , g1.destination_country\
                                  ,g1.forwading_charge\
                       from stock_picking g1 \
                       inner join stock_move g2 on g1.id=g2.picking_id \
                       where g1.state='done' and to_char(g1.date_done,'YYYY-MM-DD') <= substring(%s,1,10) \
                            and coalesce(g1.sale_id,0) <> 0 and coalesce(g2.sale_line_id,0) <> 0 \
                       group by g2.product_id,g2.sequence_line,g2.sale_line_id \
                       ,g1.destination_country,g1.forwading_charge) g \
                  on b.product_id = g.product_id and b.id = g.sale_line_id \
            left join (select n.lc_id as order_id,o1.id,o1.lc_number,o1.lc_incoterm, \
                       o2.product_id,o2.sequence_line,o2.sale_line_id, \
                       o1.rcvd_smg as lc_recvd_date, \
                       coalesce(o2.est_delivery_date,o1.lc_ship_valid_date) as lc_lsd \
                       from sale_order_letterofcredit_rel n \
                       inner join letterofcredit o1 on n.order_id = o1.id \
                       inner join letterofcredit_product_line o2 on o1.id = o2.lc_id \
                       where o1.state not in ('nonactive')) p on b.order_id = p.order_id and b.product_id = p.product_id and b.id = p.sale_line_id \
            left join res_country r on a.dest_country_id = r.id \
            left join res_port r2 on a.dest_port_id= r2.id \
            left join stock_incoterms s on a.incoterm = s.id \
            left join stock_incoterms s2 on p.lc_incoterm = s2.id \
            left join (select af2.product_id, af2.sequence_line, af2.sale_line_id, max(af2.date_expected) as date_expected, \
                              sum(case af1.type \
                                  when 'in' then af2.product_qty \
                                  when 'out' then -af2.product_qty \
                                  else 0 end) as product_qty \
                       from stock_picking af1 \
                       inner join stock_move af2 on af1.id=af2.picking_id \
                       where af1.state not in ('done','cancel') and af2.state not in ('done','cancel') \
                            and coalesce(af1.sale_id,0) <> 0 \
                       group by af2.product_id,af2.sequence_line,af2.sale_line_id) af \
                  on b.product_id = af.product_id and b.id = af.sale_line_id \
            left join product_pricelist ao on a.pricelist_id = ao.id \
            left join res_currency ap on ao.currency_id = ap.id \
                      LEFT JOIN product_template pt on c.product_tmpl_id = pt.id \
                      LEFT JOIN product_uom pu_b on b.product_uom = pu_b.id \
                      LEFT JOIN product_uom pu_pt on pt.uom_id = pu_pt.id \
                      left join ( \
                          select rp.display_name,soa.sale_line_id,rp.id from sale_order_agent soa \
                            left join res_partner rp on soa.agent_id=rp.id ) soap on b.id=soap.sale_line_id \
            left join res_partner rp_so on a.partner_id=rp_so.id \
            where a.state not in ('draft','cancel') \
            and a.date_confirm is not null \
            and to_char(a.date_confirm,'YYYY-MM-DD') <= substring(%s,1,10) \
            and ((a.date_done is null) or (to_char(a.date_done,'YYYY-MM-DD') > substring(%s,1,10))) \
            and ((a.date_cancel is null) or (to_char(a.date_cancel,'YYYY-MM-DD') > substring(%s,1,10))) \
            and ((b.date_knock_off is null) or (to_char(b.date_knock_off,'YYYY-MM-DD') > substring(%s,1,10))) \
            \
            and a.goods_type = lower(%s) \
            and a.sale_type = %s \
            and to_char(a.date_order,'YYYY-MM-DD') <= substring(%s,1,10)\
            \
            "

        s = "select aaa.cust_name,aaa.report_group,aaa.curr_name,aaa.sc_no,aaa.sc_date,aaa.prod_code,aaa.prod_name, \
            aaa.destination,aaa.uom_base_price_unit,aaa.lc_terms,aaa.lc_no,aaa.product_uom,aaa.uom_base,aaa.uom_qty, \
            aaa.uom_base_qty,aaa.amount,aaa.delivery,aaa.delivery_sort,aaa.invc_no,aaa.invc_dt,aaa.container, \
            aaa.bl_no,aaa.bl_dt,aaa.eta,aaa.lot_no,aaa.tpi,aaa.agent"
        spartner = '' 
        if data['form']['filter'] == 'filter_cust':
            for pid in data['form']['partner_id']:
                if spartner == '':
                    spartner = str(pid)
                else:
                    spartner += ','+str(pid)
        
        sproduct = '' 
        if data['form']['filter'] == 'filter_prod':
            # print data['form']['product_id'] ,"zzzzzzzzzzzzzzzzzzzzzzzzzzzzz"
            for pid in data['form']['product_id']:
                if sproduct == '':
                    sproduct = str(pid)
                else:
                    sproduct += ','+str(pid)

        sagent = '' 
        if data['form']['filter'] == 'filter_agent':
            # print data['form']['agent_id'] ,"wwwwwwwwwwwwwwwwwww"
            for pid in data['form']['agent_id']:
                if sagent == '':
                    sagent = str(pid)
                else:
                    sagent += ','+str(pid)
        
        if spartner == '':
            spartner = '0'
        spartner = '('+spartner+')' 

        if sproduct == '':
            sproduct = '0'
        sproduct = '('+sproduct+')' 
        
        if sagent == '':
            sagent = '0'
        sagent = '('+sagent+')' 
        # print sagent,"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        # sorder = "order by aaa.cust_name,aaa.report_group,aaa.curr_name,aaa.sc_date,aaa.prod_code" 

        sorder = "order by aaa.cust_name,aaa.report_group,aaa.curr_name,aaa.invc_no,aaa.sc_no,aaa.sc_date,aaa.prod_code" 
        
        if data['form']['sale_type'] == 'export':
            if data['form']['filter']=='filter_no':
                s1 += " group by coalesce(rp_ai.name,rp_so.name), \
                        coalesce(ap.name,''), \
                        coalesce(b.sequence_line,a.name), \
                        to_char(a.date_order,'DD/MM/YYYY'), \
                        c.default_code , \
                        c.name_template , \
                        coalesce(r2.destination,''), \
                        b.price_unit, \
                        \
                        coalesce(s2.code,s.code,'') , \
                        coalesce(p.lc_number,'') , \
                        b.product_uom, \
                        (case when a.sale_type = 'local' then 'BALES' else 'KGS' end), \
                        to_char(g.date_done,'Mon-YYYY'), \
                        to_char(g.date_done,'YYYYMM'), \
                        v.internal_number , \
                        to_char(v.date_invoice,'DD/MM/YYYY'), \
                        coalesce(g.container_number,'') , \
                        coalesce(v.bl_number,''), \
                        (case when coalesce(v.bl_number,'')='' then to_char(g.estimation_deliv_date,'DD/MM/YYYY') else to_char(v.bl_date,'DD/MM/YYYY') end), \
                        to_char(g.estimation_arriv_date,'DD/MM/YYYY') , \
                        coalesce(b.tpi,'') \
                        ,pu_b.name,pu_b.factor \
                        , soap.display_name \
                        ,soap.id \
                        "
                s2 += " group by coalesce(rp_so.name,rp_so.partner_alias) , \
                        coalesce(ap.name,'') ,\
                        coalesce(b.sequence_line,a.name) ,\
                        to_char(a.date_order,'DD/MM/YYYY'),\
                        c.default_code, \
                        c.name_template, \
                        coalesce(r2.name,''),\
                        b.price_unit, \
                         \
                        coalesce(s2.code,s.code,''), \
                        coalesce(p.lc_number,''), \
                        b.product_uom, \
                        (case when a.sale_type = 'local' then 'BALES' else 'KGS' end), \
                        to_char((case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end),'Mon-YYYY') , \
                        to_char((case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end),'YYYYMM'), \
                        invc_no,\
                        invc_dt,\
                        container, \
                        bl_no,\
                        bl_dt, \
                        eta, \
                        tpi \
                        ,pu_b.name,pu_b.factor \
                        , soap.display_name,soap.id \
                                having \
                                case when pu_b.name='KGS' \
                                  then sum(coalesce((b.product_uom_qty+coalesce(g.product_qty,0.0))/181.44000,0.0)) >5 \
                                  when pu_b.name='BALES' \
                                  then sum((b.product_uom_qty+coalesce(g.product_qty,0.0))) >5 \
                                  when pu_b.name='LBS' \
                                  then sum(coalesce((b.product_uom_qty+coalesce(g.product_qty,0.0))/400,0.0)) >5 \
                                  end \
                         "
 
            if data['form']['filter'] == 'filter_cust':
                s1 += " and a.partner_id in "+spartner+"\
                        group by coalesce(rp_ai.name,rp_so.name), \
                        coalesce(ap.name,''), \
                        coalesce(b.sequence_line,a.name), \
                        to_char(a.date_order,'DD/MM/YYYY'), \
                        c.default_code , \
                        c.name_template , \
                        coalesce(r2.destination,'') , \
                        b.price_unit, \
                        \
                        coalesce(s2.code,s.code,'') , \
                        coalesce(p.lc_number,'') , \
                        b.product_uom, \
                        (case when a.sale_type = 'local' then 'BALES' else 'KGS' end), \
                        to_char(g.date_done,'Mon-YYYY'), \
                        to_char(g.date_done,'YYYYMM'), \
                        v.internal_number , \
                        to_char(v.date_invoice,'DD/MM/YYYY'), \
                        coalesce(g.container_number,'') , \
                        coalesce(v.bl_number,''), \
                        (case when coalesce(v.bl_number,'')='' then to_char(g.estimation_deliv_date,'DD/MM/YYYY') else to_char(v.bl_date,'DD/MM/YYYY') end), \
                        to_char(g.estimation_arriv_date,'DD/MM/YYYY') , \
                        coalesce(b.tpi,'') \
                        ,pu_b.name,pu_b.factor  \
                        , soap.display_name \
                        ,soap.id "
                s2 += " and a.partner_id in "+spartner+"\
                        group by coalesce(rp_so.name,rp_so.partner_alias) , \
                        coalesce(ap.name,'') ,\
                        coalesce(b.sequence_line,a.name) ,\
                        to_char(a.date_order,'DD/MM/YYYY'),\
                        c.default_code, \
                        c.name_template, \
                        coalesce(r2.name,''),\
                        b.price_unit, \
                         \
                        coalesce(s2.code,s.code,''), \
                        coalesce(p.lc_number,''), \
                        b.product_uom, \
                        (case when a.sale_type = 'local' then 'BALES' else 'KGS' end), \
                        to_char((case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end),'Mon-YYYY') , \
                        to_char((case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end),'YYYYMM'), \
                        invc_no,\
                        invc_dt,\
                        container, \
                        bl_no,\
                        bl_dt, \
                        eta, \
                        tpi \
                        ,pu_b.name,pu_b.factor \
                         , soap.display_name \
                        ,soap.id \
                                having \
                                case when pu_b.name='KGS' \
                                  then sum(coalesce((b.product_uom_qty+coalesce(g.product_qty,0.0))/181.44000,0.0)) >5 \
                                  when pu_b.name='BALES' \
                                  then sum((b.product_uom_qty+coalesce(g.product_qty,0.0))) >5 \
                                  when pu_b.name='LBS' \
                                  then sum(coalesce((b.product_uom_qty+coalesce(g.product_qty,0.0))/400,0.0)) >5 \
                                  end"

            if data['form']['filter'] == 'filter_prod':
                s1 += " and b.product_id in "+sproduct+"\
                        group by coalesce(rp_ai.name,rp_so.name), \
                        coalesce(ap.name,''), \
                        coalesce(b.sequence_line,a.name), \
                        to_char(a.date_order,'DD/MM/YYYY'), \
                        c.default_code , \
                        c.name_template , \
                        coalesce(r2.destination,'') , \
                        b.price_unit, \
                        \
                        coalesce(s2.code,s.code,'') , \
                        coalesce(p.lc_number,'') , \
                        b.product_uom, \
                        (case when a.sale_type = 'local' then 'BALES' else 'KGS' end), \
                        to_char(g.date_done,'Mon-YYYY'), \
                        to_char(g.date_done,'YYYYMM'), \
                        v.internal_number , \
                        to_char(v.date_invoice,'DD/MM/YYYY'), \
                        coalesce(g.container_number,'') , \
                        coalesce(v.bl_number,''), \
                        (case when coalesce(v.bl_number,'')='' then to_char(g.estimation_deliv_date,'DD/MM/YYYY') else to_char(v.bl_date,'DD/MM/YYYY') end), \
                        to_char(g.estimation_arriv_date,'DD/MM/YYYY') , \
                        coalesce(b.tpi,'')  \
                        ,pu_b.name,pu_b.factor \
                         , soap.display_name \
                        ,soap.id  "
                s2 += " and b.product_id in "+sproduct+"\
                        group by coalesce(rp_so.name,rp_so.partner_alias) , \
                        \
                        coalesce(ap.name,'') ,\
                        coalesce(b.sequence_line,a.name) ,\
                        to_char(a.date_order,'DD/MM/YYYY'),\
                        c.default_code, \
                        c.name_template, \
                        coalesce(r2.name,''),\
                        b.price_unit, \
                         \
                        coalesce(s2.code,s.code,''), \
                        coalesce(p.lc_number,''), \
                        b.product_uom, \
                        (case when a.sale_type = 'local' then 'BALES' else 'KGS' end), \
                        to_char((case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end),'Mon-YYYY') , \
                        to_char((case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end),'YYYYMM'), \
                        invc_no,\
                        invc_dt,\
                        container, \
                        bl_no,\
                        bl_dt, \
                        eta, \
                        tpi \
                        ,pu_b.name,pu_b.factor \
                         , soap.display_name \
                         ,soap.id \
                                having \
                                case when pu_b.name='KGS' \
                                  then sum(coalesce((b.product_uom_qty+coalesce(g.product_qty,0.0))/181.44000,0.0)) >5 \
                                  when pu_b.name='BALES' \
                                  then sum((b.product_uom_qty+coalesce(g.product_qty,0.0))) >5 \
                                  when pu_b.name='LBS' \
                                  then sum(coalesce((b.product_uom_qty+coalesce(g.product_qty,0.0))/400,0.0)) >5 \
                                  end"

            if data['form']['filter'] == 'filter_agent':
                print "zzzzzzzzzzzzzzzzzzzz"
                s1 += " and soap.id in "+sagent+"\
                        group by coalesce(rp_ai.name,rp_so.name), \
                        coalesce(ap.name,''), \
                        coalesce(b.sequence_line,a.name), \
                        to_char(a.date_order,'DD/MM/YYYY'), \
                        c.default_code , \
                        c.name_template , \
                        coalesce(r2.destination,'') , \
                        b.price_unit, \
                        \
                        coalesce(s2.code,s.code,'') , \
                        coalesce(p.lc_number,'') , \
                        b.product_uom, \
                        (case when a.sale_type = 'local' then 'BALES' else 'KGS' end), \
                        to_char(g.date_done,'Mon-YYYY'), \
                        to_char(g.date_done,'YYYYMM'), \
                        v.internal_number , \
                        to_char(v.date_invoice,'DD/MM/YYYY'), \
                        coalesce(g.container_number,'') , \
                        coalesce(v.bl_number,''), \
                        (case when coalesce(v.bl_number,'')='' then to_char(g.estimation_deliv_date,'DD/MM/YYYY') else to_char(v.bl_date,'DD/MM/YYYY') end), \
                        to_char(g.estimation_arriv_date,'DD/MM/YYYY') , \
                        coalesce(b.tpi,'')  \
                        ,pu_b.name,pu_b.factor \
                         , soap.display_name,soap.id"
                s2 += " and soap.id in "+sagent+"\
                        group by coalesce(rp_so.name,rp_so.partner_alias) , \
                        \
                        coalesce(ap.name,'') ,\
                        coalesce(b.sequence_line,a.name) ,\
                        to_char(a.date_order,'DD/MM/YYYY'),\
                        c.default_code, \
                        c.name_template, \
                        coalesce(r2.name,''),\
                        b.price_unit, \
                         \
                        coalesce(s2.code,s.code,''), \
                        coalesce(p.lc_number,''), \
                        b.product_uom, \
                        (case when a.sale_type = 'local' then 'BALES' else 'KGS' end), \
                        to_char((case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end),'Mon-YYYY') , \
                        to_char((case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end),'YYYYMM'), \
                        invc_no,\
                        invc_dt,\
                        container, \
                        bl_no,\
                        bl_dt, \
                        eta, \
                        tpi \
                        ,pu_b.name,pu_b.factor \
                         , soap.display_name,soap.id \
                                having \
                                case when pu_b.name='KGS' \
                                  then sum(coalesce((b.product_uom_qty+coalesce(g.product_qty,0.0))/181.44000,0.0)) >5 \
                                  when pu_b.name='BALES' \
                                  then sum((b.product_uom_qty+coalesce(g.product_qty,0.0))) >5 \
                                  when pu_b.name='LBS' \
                                  then sum(coalesce((b.product_uom_qty+coalesce(g.product_qty,0.0))/400,0.0)) >5 \
                                  end"

            if data['form']['agent'] == 'True':
                s1 += " group by coalesce(rp_ai.name,rp_so.name), \
                        coalesce(ap.name,''), \
                        coalesce(b.sequence_line,a.name), \
                        to_char(a.date_order,'DD/MM/YYYY'), \
                        c.default_code , \
                        c.name_template , \
                        coalesce(r2.destination,'') , \
                        b.price_unit, \
                        \
                        coalesce(s2.code,s.code,'') , \
                        coalesce(p.lc_number,'') , \
                        b.product_uom, \
                        (case when a.sale_type = 'local' then 'BALES' else 'KGS' end), \
                        to_char(g.date_done,'Mon-YYYY'), \
                        to_char(g.date_done,'YYYYMM'), \
                        v.internal_number , \
                        to_char(v.date_invoice,'DD/MM/YYYY'), \
                        coalesce(g.container_number,'') , \
                        coalesce(v.bl_number,''), \
                        (case when coalesce(v.bl_number,'')='' then to_char(g.estimation_deliv_date,'DD/MM/YYYY') else to_char(v.bl_date,'DD/MM/YYYY') end), \
                        to_char(g.estimation_arriv_date,'DD/MM/YYYY') , \
                        coalesce(b.tpi,'')  \
                        ,pu_b.name,pu_b.factor \
                         , soap.display_name,soap.id"
                s2 += " group by coalesce(rp_so.name,rp_so.partner_alias) , \
                        \
                        coalesce(ap.name,'') ,\
                        coalesce(b.sequence_line,a.name) ,\
                        to_char(a.date_order,'DD/MM/YYYY'),\
                        c.default_code, \
                        c.name_template, \
                        coalesce(r2.name,''),\
                        b.price_unit, \
                         \
                        coalesce(s2.code,s.code,''), \
                        coalesce(p.lc_number,''), \
                        b.product_uom, \
                        (case when a.sale_type = 'local' then 'BALES' else 'KGS' end), \
                        to_char((case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end),'Mon-YYYY') , \
                        to_char((case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end),'YYYYMM'), \
                        invc_no,\
                        invc_dt,\
                        container, \
                        bl_no,\
                        bl_dt, \
                        eta, \
                        tpi \
                        ,pu_b.name,pu_b.factor \
                         , soap.display_name,soap.id \
                                having \
                                case when pu_b.name='KGS' \
                                  then sum(coalesce((b.product_uom_qty+coalesce(g.product_qty,0.0))/181.44000,0.0)) >5 \
                                  when pu_b.name='BALES' \
                                  then sum((b.product_uom_qty+coalesce(g.product_qty,0.0))) >5 \
                                  when pu_b.name='LBS' \
                                  then sum(coalesce((b.product_uom_qty+coalesce(g.product_qty,0.0))/400,0.0)) >5 \
                                  end"

            s += " from (" + s1 + " union all " + s2 + ") aaa " + sorder 
            self.cr.execute (s, 
                            (data['form']['date_from'], 
                            data['form']['date_to'], 
                            data['form']['goods_type'],
                            data['form']['sale_type'],
                            data['form']['date_to'], 
                            data['form']['date_to'], 
                            data['form']['date_to'], 
                            data['form']['date_to'], 
                            data['form']['date_to'], 
                            data['form']['goods_type'],
                            data['form']['sale_type'],
                            data['form']['date_to'],))
        elif data['form']['sale_type'] == 'local':
            s1 += " and a.locale_sale_type like %s" 
            s2 += " and a.locale_sale_type like %s"
            if data['form']['filter']=='filter_no':
                s1 += "group by coalesce(rp_ai.name,rp_so.name), \
                        coalesce(ap.name,''), \
                        coalesce(b.sequence_line,a.name), \
                        to_char(a.date_order,'DD/MM/YYYY'), \
                        c.default_code , \
                        c.name_template , \
                        coalesce(r2.destination,'') , \
                        b.price_unit, \
                        \
                        coalesce(s2.code,s.code,'') , \
                        coalesce(p.lc_number,'') , \
                        b.product_uom, \
                        (case when a.sale_type = 'local' then 'BALES' else 'KGS' end), \
                        to_char(g.date_done,'Mon-YYYY'), \
                        to_char(g.date_done,'YYYYMM'), \
                        v.internal_number , \
                        to_char(v.date_invoice,'DD/MM/YYYY'), \
                        coalesce(g.container_number,'') , \
                        coalesce(v.bl_number,''), \
                        (case when coalesce(v.bl_number,'')='' then to_char(g.estimation_deliv_date,'DD/MM/YYYY') else to_char(v.bl_date,'DD/MM/YYYY') end), \
                        to_char(g.estimation_arriv_date,'DD/MM/YYYY') , \
                        coalesce(b.tpi,'')  \
                        ,pu_b.name,pu_b.factor \
                        , soap.display_name \
                        ,soap.id "
                s2 += " group by coalesce(rp_so.name,rp_so.partner_alias) , \
                        \
                        coalesce(ap.name,'') ,\
                        coalesce(b.sequence_line,a.name) ,\
                        to_char(a.date_order,'DD/MM/YYYY'),\
                        c.default_code, \
                        c.name_template, \
                        coalesce(r2.name,''), \
                        b.price_unit, \
                         \
                        coalesce(s2.code,s.code,''), \
                        coalesce(p.lc_number,''), \
                        b.product_uom, \
                        (case when a.sale_type = 'local' then 'BALES' else 'KGS' end), \
                        to_char((case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end),'Mon-YYYY') , \
                        to_char((case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end),'YYYYMM'), \
                        invc_no,\
                        invc_dt,\
                        container, \
                        bl_no,\
                        bl_dt, \
                        eta, \
                        tpi  \
                        ,pu_b.name,pu_b.factor \
                        , soap.display_name \
                        ,soap.id \
                                having \
                                case when pu_b.name='KGS' \
                                  then sum(coalesce((b.product_uom_qty+coalesce(g.product_qty,0.0))/181.44000,0.0)) >5 \
                                  when pu_b.name='BALES' \
                                  then sum((b.product_uom_qty+coalesce(g.product_qty,0.0))) >5 \
                                  when pu_b.name='LBS' \
                                  then sum(coalesce((b.product_uom_qty+coalesce(g.product_qty,0.0))/400,0.0)) >5 \
                                  end"
 
            if data['form']['filter'] == 'filter_cust':
                s1 += " and a.partner_id in "+spartner+"\
                        group by coalesce(rp_ai.name,rp_so.name), \
                        coalesce(ap.name,''), \
                        coalesce(b.sequence_line,a.name), \
                        to_char(a.date_order,'DD/MM/YYYY'), \
                        c.default_code , \
                        c.name_template , \
                        coalesce(r2.destination,'') , \
                        b.price_unit, \
                        \
                        coalesce(s2.code,s.code,'') , \
                        coalesce(p.lc_number,'') , \
                        b.product_uom, \
                        (case when a.sale_type = 'local' then 'BALES' else 'KGS' end), \
                        to_char(g.date_done,'Mon-YYYY'), \
                        to_char(g.date_done,'YYYYMM'), \
                        v.internal_number , \
                        to_char(v.date_invoice,'DD/MM/YYYY'), \
                        coalesce(g.container_number,'') , \
                        coalesce(v.bl_number,''), \
                        (case when coalesce(v.bl_number,'')='' then to_char(g.estimation_deliv_date,'DD/MM/YYYY') else to_char(v.bl_date,'DD/MM/YYYY') end), \
                        to_char(g.estimation_arriv_date,'DD/MM/YYYY') , \
                        coalesce(b.tpi,'')  \
                        ,pu_b.name,pu_b.factor \
                        , soap.display_name \
                        ,soap.id "
                s2 += " and a.partner_id in "+spartner+"\
                        group by coalesce(rp_so.name,rp_so.partner_alias) , \
                        \
                        coalesce(ap.name,'') ,\
                        coalesce(b.sequence_line,a.name) ,\
                        to_char(a.date_order,'DD/MM/YYYY'),\
                        c.default_code, \
                        c.name_template, \
                        coalesce(r2.name,''),\
                        b.price_unit, \
                         \
                        coalesce(s2.code,s.code,''), \
                        coalesce(p.lc_number,''), \
                        b.product_uom, \
                        (case when a.sale_type = 'local' then 'BALES' else 'KGS' end), \
                        to_char((case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end),'Mon-YYYY') , \
                        to_char((case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end),'YYYYMM'), \
                        invc_no,\
                        invc_dt,\
                        container, \
                        bl_no,\
                        bl_dt, \
                        eta, \
                        tpi  \
                        ,pu_b.name,pu_b.factor \
                        , soap.display_name \
                        ,soap.id \
                                having \
                                case when pu_b.name='KGS' \
                                  then sum(coalesce((b.product_uom_qty+coalesce(g.product_qty,0.0))/181.44000,0.0)) >5 \
                                  when pu_b.name='BALES' \
                                  then sum((b.product_uom_qty+coalesce(g.product_qty,0.0))) >5 \
                                  when pu_b.name='LBS' \
                                  then sum(coalesce((b.product_uom_qty+coalesce(g.product_qty,0.0))/400,0.0)) >5 \
                                  end"

            if data['form']['filter'] == 'filter_prod':
                s1 += " and g.product_id in "+sproduct+"\
                        group by coalesce(rp_ai.name,rp_so.name), \
                        coalesce(ap.name,''), \
                        coalesce(b.sequence_line,a.name), \
                        to_char(a.date_order,'DD/MM/YYYY'), \
                        c.default_code , \
                        c.name_template , \
                        coalesce(r2.destination,'') , \
                        b.price_unit, \
                        \
                        coalesce(s2.code,s.code,'') , \
                        coalesce(p.lc_number,'') , \
                        b.product_uom, \
                        (case when a.sale_type = 'local' then 'BALES' else 'KGS' end), \
                        to_char(g.date_done,'Mon-YYYY'), \
                        to_char(g.date_done,'YYYYMM'), \
                        v.internal_number , \
                        to_char(v.date_invoice,'DD/MM/YYYY'), \
                        coalesce(g.container_number,'') , \
                        coalesce(v.bl_number,''), \
                        (case when coalesce(v.bl_number,'')='' then to_char(g.estimation_deliv_date,'DD/MM/YYYY') else to_char(v.bl_date,'DD/MM/YYYY') end), \
                        to_char(g.estimation_arriv_date,'DD/MM/YYYY') , \
                        coalesce(b.tpi,'')  \
                        ,pu_b.name,pu_b.factor \
                        , soap.display_name \
                        ,soap.id "
                s2 += " and g.product_id in "+sproduct+"\
                        group by coalesce(rp_so.name,rp_so.partner_alias) , \
                        \
                        coalesce(ap.name,'') ,\
                        coalesce(b.sequence_line,a.name) ,\
                        to_char(a.date_order,'DD/MM/YYYY'),\
                        c.default_code, \
                        c.name_template, \
                        coalesce(r2.name,''),\
                        b.price_unit, \
                         \
                        coalesce(s2.code,s.code,''), \
                        coalesce(p.lc_number,''), \
                        b.product_uom, \
                        (case when a.sale_type = 'local' then 'BALES' else 'KGS' end), \
                        to_char((case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end),'Mon-YYYY') , \
                        to_char((case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end),'YYYYMM'), \
                        invc_no,\
                        invc_dt,\
                        container, \
                        bl_no,\
                        bl_dt, \
                        eta, \
                        tpi  \
                        ,pu_b.name,pu_b.factor \
                        , soap.display_name \
                        ,soap.id \
                                having \
                                case when pu_b.name='KGS' \
                                  then sum(coalesce((b.product_uom_qty+coalesce(g.product_qty,0.0))/181.44000,0.0)) >5 \
                                  when pu_b.name='BALES' \
                                  then sum((b.product_uom_qty+coalesce(g.product_qty,0.0))) >5 \
                                  when pu_b.name='LBS' \
                                  then sum(coalesce((b.product_uom_qty+coalesce(g.product_qty,0.0))/400,0.0)) >5 \
                                  end"
            
            if data['form']['filter'] == 'filter_agent':
                s1 += " and soap.id in "+sagent+"\
                        group by coalesce(rp_ai.name,rp_so.name), \
                        coalesce(ap.name,''), \
                        coalesce(b.sequence_line,a.name), \
                        to_char(a.date_order,'DD/MM/YYYY'), \
                        c.default_code , \
                        c.name_template , \
                        coalesce(r2.destination,'') , \
                        b.price_unit, \
                        \
                        coalesce(s2.code,s.code,'') , \
                        coalesce(p.lc_number,'') , \
                        b.product_uom, \
                        (case when a.sale_type = 'local' then 'BALES' else 'KGS' end), \
                        to_char(g.date_done,'Mon-YYYY'), \
                        to_char(g.date_done,'YYYYMM'), \
                        v.internal_number , \
                        to_char(v.date_invoice,'DD/MM/YYYY'), \
                        coalesce(g.container_number,'') , \
                        coalesce(v.bl_number,''), \
                        (case when coalesce(v.bl_number,'')='' then to_char(g.estimation_deliv_date,'DD/MM/YYYY') else to_char(v.bl_date,'DD/MM/YYYY') end), \
                        to_char(g.estimation_arriv_date,'DD/MM/YYYY') , \
                        coalesce(b.tpi,'')  \
                        ,pu_b.name,pu_b.factor \
                         , soap.display_name,soap.id"
                s2 += " and soap.id in "+sagent+"\
                        group by coalesce(rp_so.name,rp_so.partner_alias) , \
                        \
                        coalesce(ap.name,'') ,\
                        coalesce(b.sequence_line,a.name) ,\
                        to_char(a.date_order,'DD/MM/YYYY'),\
                        c.default_code, \
                        c.name_template, \
                        coalesce(r2.name,''),\
                        b.price_unit, \
                         \
                        coalesce(s2.code,s.code,''), \
                        coalesce(p.lc_number,''), \
                        b.product_uom, \
                        (case when a.sale_type = 'local' then 'BALES' else 'KGS' end), \
                        to_char((case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end),'Mon-YYYY') , \
                        to_char((case when to_char(coalesce(b.est_delivery_date,a.max_est_delivery_date),'YYYY-MM-DD') = to_char(af.date_expected,'YYYY-MM-DD') then coalesce(b.est_delivery_date,a.max_est_delivery_date) else af.date_expected end),'YYYYMM'), \
                        invc_no,\
                        invc_dt,\
                        container, \
                        bl_no,\
                        bl_dt, \
                        eta, \
                        tpi \
                        ,pu_b.name,pu_b.factor \
                         , soap.display_name,soap.id \
                                having \
                                case when pu_b.name='KGS' \
                                  then sum(coalesce((b.product_uom_qty+coalesce(g.product_qty,0.0))/181.44000,0.0)) >5 \
                                  when pu_b.name='BALES' \
                                  then sum((b.product_uom_qty+coalesce(g.product_qty,0.0))) >5 \
                                  when pu_b.name='LBS' \
                                  then sum(coalesce((b.product_uom_qty+coalesce(g.product_qty,0.0))/400,0.0)) >5 \
                                  end"





            s += " from (" + s1 + " union all " + s2 + ") aaa " + sorder 
            self.cr.execute (s, 
                            (data['form']['date_from'], 
                            data['form']['date_to'], 
                            data['form']['goods_type'],
                            data['form']['sale_type'],
                            data['form']['locale_sale_type'],
                            data['form']['date_to'], 
                            data['form']['date_to'], 
                            data['form']['date_to'], 
                            data['form']['date_to'], 
                            data['form']['date_to'], 
                            data['form']['goods_type'],
                            data['form']['sale_type'],
                            data['form']['date_to'],
                            data['form']['locale_sale_type'],))

        res = self.cr.dictfetchall()
        # print res,"xxxxxxxxxxxxS"
        return res


report_sxw.report_sxw('report.shipment.pending.sales.report', 'report.shipment.pending.sales.wizard', 'addons/ad_sales_report/report/shipment_pending_sales_report.mako', parser=shipment_pending_sales_parser,header=False) 
report_sxw.report_sxw('report.shipment.pending.agent.report', 'report.shipment.pending.sales.wizard', 'addons/ad_sales_report/report/shipment_pending_sales_agent_report.mako', parser=shipment_pending_sales_parser,header=False) 

class shipment_pending_sales_xls(report_xls):
  no_ind = 0
  def get_no_index(self):
    self.set_no_index()
    return self.no_ind
  def set_no_index(self):
    self.no_ind += 1
    return True

  def create_source_xls(self, cr, uid, ids, data, report_xml, context=None):
    if not context:
      context = {}
    context = context.copy()
    rml_parser = self.parser(cr, uid, self.name2, context=context)
    objs = []
    rml_parser.set_context(objs, data, ids, 'xls')
    n = cStringIO.StringIO()
    wb = xlwt.Workbook(encoding='utf-8')
    self.generate_xls_report(rml_parser, data, rml_parser.localcontext['objects'], wb)
    wb.save(n)
    n.seek(0)
    return (n.read(), 'xls')
    
  def generate_xls_report(self, parser, data, obj, wb):
    c = parser.localcontext['company']
    i=0
    ws = wb.add_sheet('Export Shipment & Pending Order',cell_overwrite_ok=True)
    ws.panes_frozen = True
    ws.remove_splits = True
    ws.portrait = 0 # Landscape
    ws.fit_width_to_pages = 1
    ws.preview_magn = 60
    ws.normal_magn = 60
    ws.print_scaling=60

    title_style                     = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; pattern : pattern solid, fore_color white;')
    th_top_style                    = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; border:top thin')
    th_both_style                   = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; border:top thin, bottom thin;')
    th_bottom_ds_top_style          = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; border:bottom thin, top dashed;')
    # th_bottom_style                 = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center; border:bottom thin;')
    th_bold_style                   = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz center;')
    th_bold_style_lf                = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz left;')
    th_bottom_style                 = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz left; border:bottom thin;',num_format_str='#,##0.0000;-#,##0.0000')

    normal_style                    = xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz left;',num_format_str='#,##0.0000;-#,##0.0000')
    normal_style_float              = xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
    normal_style_float_round        = xlwt.easyxf('font: height 180, name Calibri, colour_index black; align: wrap off, vert centre, horiz right;',num_format_str='#,##0')
    normal_style_float_bold         = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz right;',num_format_str='#,##0.00;-#,##0.00')
    normal_bold_style               = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on; align: wrap off, vert centre, horiz left; ')
    normal_bold_style_b             = xlwt.easyxf('font: height 180, name Calibri, colour_index black, bold on;pattern: pattern solid, fore_color gray25; align: wrap off, vert centre, horiz left; ')
    
    subtotal_title_style            = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz left; borders: bottom thin;')
    subtotal_style                  = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz centre; borders: top thin;',num_format_str='#,##0;-#,##0')
    subtotal_style2                 = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right; borders: top thin;',num_format_str='#,##0.00;-#,##0.00')
    total_title_style               = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz centre;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;')
    total_style                     = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz centre;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.0000;(#,##0.0000)')
    total_style2                    = xlwt.easyxf('font: name Times New Roman, colour_index black, bold on; align: wrap off, vert centre, horiz right;pattern: pattern solid, fore_color gray25; borders: top thin, bottom thin;',num_format_str='#,##0.00;(#,##0.00)')
    subtittle_top_and_bottom_style  = xlwt.easyxf('font: height 240, name Times New Roman, colour_index black, bold off, italic on; align: wrap off, vert centre, horiz left; pattern: pattern solid, fore_color white;')

    # add_info = data['form']['with_invoice_information']
    date_start = data['form']['date_from']
    date_end = data['form']['date_to']
    sale_type= data['form']['sale_type'].upper()
    # rm_goods_type = data['form']['goods_type']=='raw'
    # if data['form']['foc']:
    #   foc_text=" ( FOC )"
    # else:
    #   foc_text=""
    # # if rm_goods_type:
    ws.write_merge(0,0,0,20, "PT BITRATEX INDUSTRIES" , title_style)
    ws.write_merge(1,1,0,20, sale_type+ " SHIPMENTS & PENDING ORDERS" , title_style)
    ws.write_merge(2,2,0,20, "Period " +date_start+ "To" + date_end , title_style)
    # if data['form']['filter_date']=='as_of':
    #   ws.write_merge(2,2,0, add_info and 28 or 20, "As Of "+datetime.strptime(data['form']['as_of_date'],"%Y-%m-%d").strftime("%d/%m/%Y"), title_style)
    # else:
    #   ws.write_merge(2,2,0, add_info and 28 or 20, "FROM "+datetime.strptime(date_start,"%Y-%m-%d").strftime("%d/%m/%Y")+" TO "+datetime.strptime(date_end,"%Y-%m-%d").strftime("%d/%m/%Y"), title_style)
    ws.write_merge(4,5,0,2, "", th_both_style)
    ws.write_merge(4,4,3,4, "ORDER", th_top_style)
    ws.write(4,8, "PRICE L/C", th_top_style)
    ws.write(4,10, "QTY", th_top_style)
    ws.write(5,3, "NO.", th_bottom_ds_top_style)
    ws.write(5,4, "DATE", th_bottom_ds_top_style)
    ws.write_merge(4,5,5,5, "PRODUCT", th_both_style)
    ws.write_merge(4,5,6,6, "DEST", th_both_style)
    ws.write_merge(4,5,7,7, "CURR", th_both_style)
    ws.write(5,8, "/KGS TERMS", th_bottom_ds_top_style)
    ws.write_merge(4,5,9,9, "L/C NO.", th_both_style)
    ws.write(5,10, "KGS", th_bottom_ds_top_style)
    ws.write_merge(4,5,11,11, "AMOUNT", th_both_style)
    ws.write_merge(4,5,12,12, "DELIVERY", th_both_style)
     
    ws.write_merge(4,5,13,13, "INVC NO", th_both_style)
    ws.write_merge(4,5,14,14, "INVC DT", th_both_style)
    ws.write_merge(4,5,15,15, "CONTAINER", th_both_style)
    ws.write_merge(4,5,16,16, "B/L NO", th_both_style)
    ws.write_merge(4,5,17,17, "B/L DATE", th_both_style)
    ws.write_merge(4,5,18,18, "ETA", th_both_style)
    ws.write_merge(4,5,19,19, "LOT", th_both_style)
    ws.write_merge(4,5,20,20, "TPI", th_both_style)

    result=parser._get_view(data)
    cust_uom_base_qty = 0.0
    cust_amount = 0.0
    cust_item_count = 0
    group_uom_base_qty = 0.0
    group_amount = 0.0
    group_item_count = 0
    subgroup_uom_base_qty = 0.0
    subgroup_amount = 0.0
    subgroup_item_count = 0
    grand_uom_base_qty = 0.0
    grand_amount = 0.0
    grand_item_count = 0.0
    
    old_cust_name = "None"
    old_group_name = "None"
    old_subgroup_name = "None"
    cust_name = "None"
    group_name = "None"
    subgroup_name = "None"
    # row_count=6
    # max_width_col_0=len("NO.")
    # max_width_col_1=len("NO.")
    # max_width_col_2=len("NO.")
    max_width_col_3=len("NO.")
    max_width_col_4=len("Date.")
    max_width_col_5=len("Product")
    max_width_col_6=len("Dest")
    max_width_col_7=len("Curr.")
    max_width_col_8=len("/KGS TERMS")
    max_width_col_9=len("L/C NO.")
    max_width_col_10=len("KGS")
    max_width_col_11=len("AMOUNT")
    max_width_col_12=len("Delivery")
    max_width_col_13=len("INVC NO")
    max_width_col_14=len("INVC DT")
    max_width_col_15=len("CONTAINER")
    max_width_col_16=len("B/L NO")
    max_width_col_17=len("B/L DATE")
    max_width_col_18=len("ETA")
    max_width_col_19=len("LOT")
    max_width_col_20=len("TPI")

    
    result_grouped={}
    row_count=6
    for cust_name, lines in groupby(result, key=itemgetter('cust_name')):
      print cust_name,"xxxxxxxxxxxxxxxxxxxxx"
      ws.write_merge(row_count,row_count,0,4," "+cust_name, th_bold_style_lf)
      row_count+=1
      total_customer_amount=0.0000
      total_customer_qty=0.0000

    

      for report_group, line_group in groupby(lines, key=itemgetter('report_group')):
        if (report_group or 0) == 1:
          group_name = "SHIPMENTS:"
        elif (report_group or 0) == 2:
          group_name = "PENDING ORDERS:"
        elif (report_group or 0) == 3:
          group_name = "AMMENDED ORDERS:"
        else:
          group_name = "CANCELLED ORDERS:"
        ws.write(row_count,1,group_name, th_bold_style)
        row_count+=1
        total_group_amount=0.0000
        total_group_qty=0.0000
        for curr_name, line_curr in groupby(line_group, key=itemgetter('curr_name')):
          ws.write(row_count,2,curr_name,th_bold_style)
          row_count+=1
          total_curr_amount=0.0000
          total_curr_qty=0.0000
          for line_datas in line_curr:
            ws.write(row_count,3,line_datas['sc_no'],normal_style)
            if len(line_datas['sc_no'] or line_datas['sc_no'] or '' )>max_width_col_3:
              max_width_col_3=len(line_datas['sc_no'])
            ws.write(row_count,4,line_datas['sc_date'],normal_style)
            if len(line_datas['sc_date'] or line_datas['sc_date'] or '')>max_width_col_4:
              max_width_col_4=len(line_datas['sc_date'])
            ws.write(row_count,5,line_datas['prod_name'],normal_style)
            if len(line_datas['prod_name'] or line_datas['product_name'])>max_width_col_5:
              max_width_col_5=len(line_datas['prod_name'])
            ws.write(row_count,6,line_datas['destination'],normal_style)
            if len(line_datas['destination'] or line_datas['destination'])>max_width_col_6:
              max_width_col_6=len(line_datas['destination'])
            ws.write(row_count,7,line_datas['curr_name'],normal_style)
            if len(line_datas['curr_name'] or line_datas['curr_name'])>max_width_col_7:
              max_width_col_7=len(line_datas['curr_name'])
            # ws.write(row_count,8,str(round(line_datas['uom_base_price_unit'], 4))+" "+line_datas['lc_terms'] ,normal_style)
            ws.write(row_count,8,str(format(line_datas['uom_base_price_unit'], '.4f'))+" "+line_datas['lc_terms'] ,normal_style)
            # if len(line_datas['uom_base_price_unit'] or line_datas['uom_base_price_unit'] or '')>max_width_col_8:
            #   max_width_col_8=len(line_datas['uom_base_price_unit'])
            ws.write(row_count,9,line_datas['lc_no'],normal_style)
            if len(line_datas['lc_no'] or line_datas['lc_no'] or '')>max_width_col_9:
              max_width_col_9=len(line_datas['lc_no'])
            ws.write(row_count,10,line_datas['uom_base_qty'],normal_style)
            # if len(line_datas['uom_base_qty'] or line_datas['uom_base_qty'] or '')>max_width_col_10:
            #   max_width_col_10=len(line_datas['uom_base_qty'])
            ws.write(row_count,11,line_datas['amount'],normal_style)
            # if len(line_datas['amount'] or line_datas['amount'] or '')>max_width_col_11:
            #   max_width_col_11=len(line_datas['amount'])
            ws.write(row_count,12,line_datas['delivery'],normal_style)
            if len(line_datas['delivery'] or line_datas['delivery'] or '')>max_width_col_12:
              max_width_col_12=len(line_datas['delivery'])
            ws.write(row_count,13,line_datas['invc_no'],normal_style)
            if len(line_datas['invc_no'] or line_datas['invc_no'] or '')>max_width_col_13:
              max_width_col_13=len(line_datas['invc_no'])
            ws.write(row_count,14,line_datas['invc_dt'],normal_style)
            if len(line_datas['invc_dt'] or line_datas['invc_dt'] or '')>max_width_col_14:
              max_width_col_14=len(line_datas['invc_dt'])
            ws.write(row_count,15,line_datas['container'],normal_style)
            if len(line_datas['container'] or line_datas['container'] or '')>max_width_col_15:
              max_width_col_15=len(line_datas['container'])
            ws.write(row_count,16,line_datas['bl_no'],normal_style)
            if len(line_datas['bl_no'] or line_datas['bl_no'] or '')>max_width_col_16:
              max_width_col_16=len(line_datas['bl_no'])
            ws.write(row_count,17,line_datas['bl_dt'],normal_style)
            if len(line_datas['bl_dt'] or line_datas['bl_dt'] or '')>max_width_col_17:
              max_width_col_16=len(line_datas['bl_dt'])
            ws.write(row_count,18,line_datas['eta'],normal_style)
            if len(line_datas['eta'] or line_datas['eta']  or '')>max_width_col_18:
              max_width_col_18=len(line_datas['eta'])
            ws.write(row_count,19,line_datas['lot_no'],normal_style)
            if len(line_datas['lot_no'] or line_datas['lot_no']  or '')>max_width_col_19:
              max_width_col_19=len(line_datas['lot_no'])
            ws.write(row_count,20,line_datas['tpi'],normal_style)
            if len(line_datas['tpi'] or line_datas['tpi'])>max_width_col_20:
              max_width_col_20=len(line_datas['tpi'])
            total_curr_qty=total_curr_qty+line_datas['uom_base_qty']
            total_curr_amount=total_curr_amount+line_datas['amount']
            row_count+=1
          ws.write(row_count,2,"Total of USD",th_bottom_style)
          ws.write(row_count,3,"",th_bottom_style)
          ws.write(row_count,4,"",th_bottom_style)
          ws.write(row_count,5,"",th_bottom_style)
          ws.write(row_count,6,"",th_bottom_style)
          ws.write(row_count,7,"",th_bottom_style)
          ws.write(row_count,8,"",th_bottom_style)
          ws.write(row_count,9,"",th_bottom_style)
          ws.write(row_count,10,total_curr_qty,th_bottom_style)
          ws.write(row_count,11,total_curr_amount,th_bottom_style)
          ws.write(row_count,12,"",th_bottom_style)
          ws.write(row_count,13,"",th_bottom_style)
          ws.write(row_count,14,"",th_bottom_style)
          ws.write(row_count,15,"",th_bottom_style)
          ws.write(row_count,16,"",th_bottom_style)
          ws.write(row_count,17,"",th_bottom_style)
          ws.write(row_count,18,"",th_bottom_style)
          ws.write(row_count,19,"",th_bottom_style)
          ws.write(row_count,20,"",th_bottom_style)
          total_group_qty=total_group_qty+total_curr_qty
          total_group_amount=total_group_amount+total_curr_amount
          row_count+=1
        ws.write(row_count,1,"Total of Pending Orders",th_bottom_style)
        ws.write(row_count,2,"",th_bottom_style)
        ws.write(row_count,3,"",th_bottom_style)
        ws.write(row_count,4,"",th_bottom_style)
        ws.write(row_count,5,"",th_bottom_style)
        ws.write(row_count,6,"",th_bottom_style)
        ws.write(row_count,7,"",th_bottom_style)
        ws.write(row_count,8,"",th_bottom_style)
        ws.write(row_count,9,"",th_bottom_style)
        ws.write(row_count,10,total_group_qty,th_bottom_style)
        ws.write(row_count,11,total_curr_amount,th_bottom_style)
        ws.write(row_count,12,"",th_bottom_style)
        ws.write(row_count,13,"",th_bottom_style)
        ws.write(row_count,14,"",th_bottom_style)
        ws.write(row_count,15,"",th_bottom_style)
        ws.write(row_count,16,"",th_bottom_style)
        ws.write(row_count,17,"",th_bottom_style)
        ws.write(row_count,18,"",th_bottom_style)
        ws.write(row_count,19,"",th_bottom_style)
        ws.write(row_count,20,"",th_bottom_style)
        total_customer_qty=total_customer_qty+total_group_qty
        total_customer_amount=total_customer_amount+total_group_amount
        row_count+=1
      ws.write(row_count,0," Total of "+cust_name,th_bottom_style)
      ws.write(row_count,1,"",th_bottom_style)
      ws.write(row_count,2,"",th_bottom_style)
      ws.write(row_count,3,"",th_bottom_style)
      ws.write(row_count,4,"",th_bottom_style)
      ws.write(row_count,5,"",th_bottom_style)
      ws.write(row_count,6,"",th_bottom_style)
      ws.write(row_count,7,"",th_bottom_style)
      ws.write(row_count,8,"",th_bottom_style)
      ws.write(row_count,9,"",th_bottom_style)
      ws.write(row_count,10,total_customer_qty,th_bottom_style)
      ws.write(row_count,11,total_customer_amount,th_bottom_style)
      ws.write(row_count,12,"",th_bottom_style)
      ws.write(row_count,13,"",th_bottom_style)
      ws.write(row_count,14,"",th_bottom_style)
      ws.write(row_count,15,"",th_bottom_style)
      ws.write(row_count,16,"",th_bottom_style)
      ws.write(row_count,17,"",th_bottom_style)
      ws.write(row_count,18,"",th_bottom_style)
      ws.write(row_count,19,"",th_bottom_style)
      ws.write(row_count,20,"",th_bottom_style)
      row_count+=1

    # ws.col(0).width = 256 * int(max_width_col_0*.2)
    # ws.col(1).width = 256 * int(max_width_col_1*3)
    # ws.col(2).width = 256 * int(max_width_col_2*3)
    ws.col(3).width = 256 * int(max_width_col_3*1.4)
    ws.col(4).width = 256 * int(max_width_col_4*1.4)
    ws.col(5).width = 256 * int(max_width_col_5*1.4)
    ws.col(6).width = 256 * int(max_width_col_6*.6)
    ws.col(7).width = 256 * int(max_width_col_7*1.4)
    ws.col(8).width = 256 * int(max_width_col_8*1.4)
    ws.col(9).width = 256 * int(max_width_col_9*0.5)
    ws.col(10).width = 256 * int(max_width_col_10*5)
    ws.col(11).width = 256 * int(max_width_col_11*3)
    ws.col(12).width = 256 * int(max_width_col_12*1.4)
    ws.col(13).width = 256 * int(max_width_col_13*1.4)
    ws.col(14).width = 256 * int(max_width_col_14*1.4)
    ws.col(15).width = 256 * int(max_width_col_15*1.4)
    ws.col(16).width = 256 * int(max_width_col_16*1.4)
    ws.col(17).width = 256 * int(max_width_col_17*1.4)
    ws.col(18).width = 256 * int(max_width_col_18*1.4)
    ws.col(19).width = 256 * int(max_width_col_19*1.4)
    ws.col(20).width = 256 * int(max_width_col_20*1.4)



      # key_cust=cust_name
      # if key_cust not in result_grouped:
      #   result_grouped.update({key_cust:{}})
      #   for line in lines:

      # # for line in result:
      #     # key_cust=line['cust_name'] or ''
      #     if (line['report_group'] or 0) == 1:
      #       group_name = "SHIPMENTS:"
      #     elif (line['report_group'] or 0) == 2:
      #       group_name = "PENDING ORDERS:"
      #     elif (line['report_group'] or 0) == 3:
      #       group_name = "AMMENDED ORDERS:"
      #     else:
      #       group_name = "CANCELLED ORDERS:"
      #     key_groupname=group_name
      #     if key_groupname not in result_grouped[key_cust]:
      #       result_grouped[key_cust].update({key_groupname:{}})

      #     for customer in sorted(result_grouped.keys(),key=lambda l:l[1]):
      #       ws.write(row_count,0, customer or '', normal_style)
      #       row_count+=1

        # for group_name in result_grouped[key_cust].keys():
        #   ws.write(row_count,1, group_name, normal_style)
        #   row_count+=1
        
        # print key_data,"zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"
        # lines=result_grouped[key_cust][key_data]
        # print lines,"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        # for line in lines:
        #   ws.write(row_count,1, line[key_groupname], normal_style)



      # cust_name=line['cust_name'] or ''
      # key=cust_name
      # if key not in result_cust:
      #   result_cust.update({key:[]})
      #   result_cust[key].append(line)
      #   ws.write(row_count,0, key or '', normal_style)
      #   row_count+=1
      #   result_group_name={}
      #   for line_group_name  in sorted(result_cust.keys(),key=lambda l:l[1]):
      #     lines = sorted(result_cust[line][line_group_name], key=lambda x:x[1])
      #     if (lines['report_group'] or 0) == 1:
      #       group_name = "SHIPMENTS:"
      #     elif (lines['report_group'] or 0) == 2:
      #       group_name = "PENDING ORDERS:"
      #     elif (lines['report_group'] or 0) == 3:
      #       group_name = "AMMENDED ORDERS:"
      #     else:
      #       group_name = "CANCELLED ORDERS:"
      #     key_groupname=group_name
      #     if key_groupname not in result_group_name:
      #       result_group_name.update(key_groupname)
      #       result_group_name[key_groupname].append(line_group_name)
      #       ws.write(row_count,1, key_groupname or '', normal_style)
      #       row_count+=1



        # for key_loc in sorted(result_grouped.keys(),key=lambda l:l[1]):
      # old_cust_name = cust_name

      # if group_name != old_group_name:
      #   old_group_name = group_name


    # if not data['form']['foc']:
    #   ws.write_merge(4,4,12,19, "RECEIPT", th_top_style)
    #   ws.write(5,12, "BALES", th_bottom_style)
    #   ws.write(5,13, "NET WT Kg", th_bottom_style)
    #   ws.write(5,14, "%", th_bottom_style)
    #   ws.write(5,15, "COMP WT.Kg", th_bottom_style)
    #   ws.write(5,16, "USD", th_bottom_style)
    #   ws.write(5,17, "AMOUNT", th_bottom_style)
    #   ws.write(5,18, "UNIT COST", th_bottom_style)
    #   ws.write(5,19, "EQ.USD", th_bottom_style)
    #   ws.write_merge(4,5,20,20, "REMARK", th_both_style)
    #   if add_info:
    #     ws.write_merge(4,4,21,28, "INVOICE RECEIPT", th_top_style)
    #     ws.write(5,21, "INV. NO.", th_bottom_style)
    #     ws.write(5,22, "COST", th_bottom_style)
    #     ws.write(5,23, "PAYMENT", th_bottom_style)
    #     ws.write(5,24, "VOUCHER", th_bottom_style)
    #     ws.write(5,25, "CONTRACT", th_bottom_style)
    #     ws.write(5,26, "BANK", th_bottom_style)
    #     ws.write(5,27, "DD OF PAY", th_bottom_style)
    #     ws.write(5,28, "DIFF RATE", th_bottom_style)
    # else :
    #   ws.write_merge(4,4,12,18, "RECEIPT", th_top_style)
    #   # ws.write(5,12, "BALES", th_bottom_style)
    #   ws.write(5,12, "NET WT Kg", th_bottom_style)
    #   ws.write(5,13, "%", th_bottom_style)
    #   ws.write(5,14, "COMP WT.Kg", th_bottom_style)
    #   ws.write(5,15, "USD", th_bottom_style)
    #   ws.write(5,16, "AMOUNT", th_bottom_style)
    #   ws.write(5,17, "UNIT COST", th_bottom_style)
    #   ws.write(5,18, "EQ.USD", th_bottom_style)
    #   ws.write_merge(4,5,19,19, "REMARK", th_both_style)
    #   if add_info:
    #     ws.write_merge(4,4,20,27, "INVOICE RECEIPT", th_top_style)
    #     ws.write(5,20, "INV. NO.", th_bottom_style)
    #     ws.write(5,21, "COST", th_bottom_style)
    #     ws.write(5,22, "PAYMENT", th_bottom_style)
    #     ws.write(5,23, "VOUCHER", th_bottom_style)
    #     ws.write(5,24, "CONTRACT", th_bottom_style)
    #     ws.write(5,25, "BANK", th_bottom_style)
    #     ws.write(5,26, "DD OF PAY", th_bottom_style)
    #     ws.write(5,27, "DIFF RATE", th_bottom_style)  




shipment_pending_sales_xls('report.xls.shipment.pending.sales.report','report.shipment.pending.sales.wizard','addons/ad_sales_report/report/shipment_pending_sales_report.mako', parser=shipment_pending_sales_parser,header=False)
