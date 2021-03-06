import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from datetime import datetime
import locale
    
class delivery_order_parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(delivery_order_parser, self).__init__(cr, uid, name, context=context)        
        #======================================================================= 
        self.line_no = 0
        self.localcontext.update({
            'time': time,
            'convert_uom_to_bales' : self.convert_uom_to_bales,
            # 'tot_qty':self._tot_qty,
            'get_movelines_group':self._get_movelines_group,
            'get_totqty_kgs':self._get_totqty_kgs,
            'get_totqty_bales':self._get_totqty_bales,
            # 'get_loc1':self._get_loc1,
            # 'get_ship_to':self._get_ship_to,
            'get_autoIncrement':self._get_autoIncrement,
            'get_address':self.get_address,
            'get_gross_wt' : self._get_gross_wt, 
        })

    # def _get_loc1(self,num_obj):
    #     if num_obj:
    #         locale.setlocale(locale.LC_NUMERIC, 'English')

    def get_address(self, partner_obj):
        if partner_obj:
            partner_address = ''
            partner_address += partner_obj.street and partner_obj.street + '\n ' or ''
            partner_address += partner_obj.street2 and partner_obj.street2 +'\n ' or ''
            partner_address += partner_obj.street3 and partner_obj.street3 +'\n ' or ''
            partner_address += partner_obj.city and partner_obj.city +' ' or ''
            partner_address += partner_obj.zip and partner_obj.zip +', ' or ''
            partner_address += partner_obj.country_id.name and partner_obj.country_id.name or ''

            return  partner_address.replace('\n','<br />')
        else:
            return False
    
    def _get_autoIncrement(self):
        rec=0
        pStart = 1  
        pInterval = 1 
        if (rec == 0):  
            rec = pStart  
        else:  
            rec += pInterval  
        return rec

    def convert_uom_to_bales(self,qty,uom_source):
        cr = self.cr
        uid = self.uid
        bale = self.pool.get('product.uom').search(cr,uid,[('name','=','BALES')])
        qty_result = self.pool.get('product.uom')._compute_qty(cr, uid, uom_source, qty, to_uom_id=bale and bale[0] or False)
        return qty_result

    # def _get_invline_totprice(self,invline_obj):
    #     sumqty=0
    #     sumtotprice=0
    #     for a in invline_obj:
    #         sumqty=sumqty+a.quantity
    #         sumtotprice=sumtotprice+(a.quantity*a.price_unit)
    #     sumlocqty=locale.format('%.3f', sumqty, True)
    #     sumloctotprice=locale.format('%.2f', sumtotprice, True )
    #     return sumlocqty,sumloctotprice,sumtotprice

    # def loc1(self):
    #     locale.setlocale(locale.LC_NUMERIC, 'English')

    def _get_totqty_kgs(self,qty_obj):
        qtykgs_bale=0
        qtykgs_bale1=0
        qtykgs_bale2=0
        qty_uop=0
        for a in qty_obj:
            if a.product_uom.name=="BALES":
                qtykgs_bale+=a.product_qty/(2.2046/400)
            if a.product_uom.name=="KGS":
                qtykgs_bale1+=a.product_qty
            if a.product_uom.name=="LBS":
                qtykgs_bale2+=a.product_qty/2.2046
            tot_qtykgs=qtykgs_bale+qtykgs_bale1+qtykgs_bale2
            qty_uop+=a.product_uop_qty
        #totqtykgs_loc=locale.format('%.2f', tot_qtykgs, True )
        #qty_uop_loc=locale.format('%.2f', qty_uop, True )
        return tot_qtykgs,qty_uop

    def _get_gross_wt(self,move_lines):
        gross_wt = 0.0
        kgs_uop_id = self.pool.get('product.uom').search(self.cr,self.uid,[('name','=','KGS')])
        for line in move_lines:
            try:
                gross_wt+=line.gross_weight and line.gross_weight or \
                        self.pool.get('product.uom')._compute_qty(self.cr, self.uid, line.product_uom.id, line.product_qty, to_uom_id=kgs_uop_id and kgs_uop_id[0] or False)
            except:
                gross_wt+=0
        return gross_wt

    def _get_totqty_bales(self,qty_obj):
        qtybale_kgs=0
        qtybale_kgs2=0
        qtybale_kgs3=0
        for a in qty_obj:
            if a.product_uom.name=="KGS":
                qtybale_kgs+=a.product_qty*(2.2046/400)
            if a.product_uom.name=="BALES":
                qtybale_kgs2+=a.product_qty
            if a.product_uom.name=="LBS":
                qtybale_kgs3+=a.product_qty/400
            tot_qtybales=qtybale_kgs+qtybale_kgs2+qtybale_kgs3
        return tot_qtybales

    # def _get_movelines_group(self,movelines_obj):
    #     for line in movelines_obj:
    #         desc=line.product_id and line.product_id.name
    #         lot=line.tracking_id and line.tracking_id.name
    #         uop=line.product_uop and line.product_uop.name
    #         uop_qty=line.product_uop_qty
    #         prod_qty=line.product_qty
    #         uom_qty=line.product_uom and line.product_uom.name
    #     return desc,lot,uop,uop_qty,prod_qty,uom_qty


    
    def _get_movelines_group(self,movelines_obj):
        res=[]
        prod_group={}
        no=0
        for line in movelines_obj:
            key=(line.sequence_line and line.sequence_line and line.sequence_line, line.product_id and line.product_id.id or False,line.tracking_id and line.tracking_id.id or False, line.product_uop and line.product_uop.name or False)
            if not (key in prod_group.keys()):
                no+=1
                prod_group[key]=[0,"",0,0,"","","","",{}]
            prod_group[key][0]=no #5
            prod_group[key][1]=line.tracking_id and line.tracking_id.name
            prod_group[key][2]+=int(line.product_uop_qty)
            prod_group[key][3]+=line.product_qty
            prod_group[key][4]=line.product_uom.name
            prod_group[key][5]=line.product_id and line.product_id.name #0
            prod_group[key][6]=line.product_uop and line.product_uop.packing_type and line.product_uop.packing_type.name
            prod_group[key][7]=line.sale_line_id and line.sale_line_id.sequence_line or ''
            for x in line.stock_move_line_ids:
                if x.product_id and x.product_id.id not in prod_group[key][8].keys():
                    prod_group[key][8].update({x.product_id.id:["",0.0,""]})
                prod_group[key][8][x.product_id.id][0] = x.description or x.product_id.name or ""
                prod_group[key][8][x.product_id.id][1] += (x.product_qty or 0.0)
                prod_group[key][8][x.product_id.id][2] = x.product_uom and x.product_uom.name or ""
        for x in prod_group.keys():
            res.append(prod_group[x])
            result=sorted(res,key=lambda res:res[5])
        return result


    # def _get_movelines_group(self,movelines_obj):
    #     res=[]
    #     prod_group={}
    #     for line in movelines_obj:
    #         key=(line.product_id and line.product_id.name,line.tracking_id and line.tracking_id.name)
    #         if key not in prod_group:
    #             prod_group[key]=["","",0,0,""]
    #         prod_group[key][0]=line.product_id and line.product_id.name
    #         prod_group[key][1]=line.tracking_id and line.tracking_id.name
    #         prod_group[key][2]+=line.product_uop_qty
    #         prod_group[key][3]+=line.product_qty
    #         prod_group[key][4]=line.product_uom.name

    #     for x in prod_group.keys():
    #         res.append(prod_group[x])
    #     return res



    # def _get_ship_to(self,to_obj):
    #     if to_obj.sale_type=="local":
    #         tujuan=to_obj.partner_id and to_obj.partner_id.name  or ''
    # #         #     alamat=a.partner_id and a.partner_id.street
    # #         #     alamat2=a.partner_id and a.partner_id.street2
    # #         #     alamat3=a.partner_id and a.partner_id.street3
    # #         #     alamat4=a.partner_id and a.partner_id.city
    # #         # elif a.sale_type=="export":
    # #         #     tujuan=a.container_book_id and a.container_book_id.port_form  and a.container_book_id.port_form.name
    # #         #     alamat=a.container_book_id and a.container_book_id.port_form and a.container_book_id.port_form.country
    # #         #     alamat2=""
    # #         #     alamat3=""
    # #         #     alamat4=""
    #     return tujuan


report_sxw.report_sxw('report.sale.shipping.x', 'stock.picking.out', 'ad_picking_report/delivery_order_form.mako', parser=delivery_order_parser,header='false') 