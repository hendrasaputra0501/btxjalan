import time
from report import report_sxw
from osv import osv,fields
from report.render import render
import pooler
from tools.translate import _
from ad_num2word_id import num2word
import locale
from collections import OrderedDict

class account_print_invoice_parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(account_print_invoice_parser, self).__init__(cr, uid, name, context=context)        
        #======================================================================= 
        self.line_no = 0
        self.localcontext.update({
            'time': time,
            'get_totline_amt': self._get_totline_amt,
            'get_totline': self._get_totline,
            'call_num2word':self._call_num2word,
            'get_totline2':self._get_totline2,
            'get_address':self.get_address,
            'get_price_actual':self.get_price_actual,
            'get_label':self._get_label,
            'get_lc_number':self._get_lc_number,
        })

    def _get_label(self,obj):
        lc_objs = []
        if obj.sale_ids and obj.picking_ids and (obj.sale_ids[0].payment_method=='lc' or obj.sale_ids[0].payment_method=='tt') :
            for picking in obj.picking_ids:
                if picking.lc_ids:
                    for lc in picking.lc_ids:
                        # if lc not in lc_objs and lc.state not in ['canceled','nonactive','closed']:
                            lc_objs.append(lc)
        label_dict = {}
        for lc in lc_objs:
            label_on_lc = eval(lc.label_print)
            if label_on_lc:
                for k,v in label_on_lc.items():
                    if k not in label_dict:
                        label_dict.update({k:v})
        if not lc_objs and not label_dict:
            label_dict = (eval(obj.label_print)).copy()
        return label_dict

    def _get_lc_number(self, obj):
        lc_ids = []
        for picking in obj.picking_ids:
            for lc in picking.lc_ids:
                if lc.lc_type=='in' and lc not in lc_ids:
                    lc_ids.append(lc)
        
        arr_temp_lc = []
        if lc_ids:
            for lc in lc_ids:
                arr_temp_lc.append(lc.lc_number)

        return arr_temp_lc and '<br/>'.join(arr_temp_lc) or ''

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


    def _get_totline_amt(self,invline_obj):
        tot_amt=0
        tot_qty=0
        qty1=0
        qty2=0
        qty3=0
        for a in invline_obj:
            tot_amt=tot_amt+a.price_subtotal
            tot_qty+=a.quantity
            if a.uos_id.name=="BALES":
                qty1+=a.quantity/(2.2046/400)
            if a.uos_id.name=="KGS":
                qty2+=a.quantity
            if a.uos_id.name=="LBS":
                qty3+=a.quantity/2.2046
            tot_qtykgs=qty1+qty2+qty3
            # totqtykgs_loc=locale.format('%.2f', tot_qtykgs, True ) 
        return tot_amt,tot_qty,tot_qtykgs

        # def _get_totqty_kgs(self,qty_obj):
        # qtykgs_bale=0
        # qtykgs_bale1=0
        # qtykgs_bale2=0
        # qty_uop=0
        # for a in qty_obj:
        #     if a.product_uom.name=="BALES":
        #         qtykgs_bale+=a.product_qty/(2.2046/400)
        #     if a.product_uom.name=="KGS":
        #         qtykgs_bale1+=a.product_qty
        #     if a.product_uom.name=="LBS":
        #         qtykgs_bale2+=a.product_qty/2.2046
        #     tot_qtykgs=qtykgs_bale+qtykgs_bale1+qtykgs_bale2
        #     qty_uop+=a.product_uop_qty
        # #totqtykgs_loc=locale.format('%.2f', tot_qtykgs, True )
        # #qty_uop_loc=locale.format('%.2f', qty_uop, True )
        # return tot_qtykgs,qty_uop

    def _get_totline(self,invline_obj):
        res=[]
        totline_group={}
        for line in invline_obj:
            key=(line.product_id,line.account_id)
            if key not in totline_group:
                totline_group[key]=["","","",0,0,0]
            totline_group[key][0]=line.invoice_id and line.invoice_id.picking_ids[0] and line.invoice_id.picking_ids[0].container_book_id and line.invoice_id.picking_ids[0].container_book_id.goods_lines[0] and line.invoice_id.picking_ids[0].container_book_id.goods_lines[0].marks_nos
            totline_group[key][1]=line.name
            totline_group[key][2]=line.uos_id and line.uos_id.name
            totline_group[key][3]+=int(line.quantity)
            totline_group[key][4]+=int(line.price_unit)
            totline_group[key][5]+=int(line.price_subtotal)

        for x in totline_group.keys():
            res.append(totline_group[x])
        return res
        #print "hasil dictionary", totline_group
        #return totline_group

    def get_price_actual(self,tax_lines,price_unit):
        if not tax_lines:
            price=price_unit
        else:
            price=price_unit
            for tax in tax_lines:
                if tax.price_include:
                    if tax.type=='percent' and not tax.inside_berikat:
                        price=price/(1.0+tax.amount)
        return price

    def _get_mark_nos(self, invoice_line):
        mark_nos = ""
        if invoice_line.invoice_id and invoice_line.invoice_id.picking_ids and invoice_line.invoice_id.picking_ids[0].container_book_id:
            for line in invoice_line.invoice_id.picking_ids[0].container_book_id.goods_lines:
                cek = True
                cek = cek and (line.product_id == invoice_line.product_id)
                cek = cek and ((line.product_uop and line.product_uop.id or False) == (invoice_line.move_line_ids and invoice_line.move_line_ids.product_uop and invoice_line.move_line_ids[0].product_uop.id or False))
                if cek:
                    mark_nos = line.marks_nos_pl
                    break
        return mark_nos

    def _get_packing_type(self, move_lines):
        cr = self.cr
        uid = self.uid
        container_book_pool = self.pool.get("container.booking")
        container_book_line_pool = self.pool.get("container.booking.line")
        packing_type_names = []
        if move_lines:
            container_booking_ids = [x.picking_id.container_book_id.id for x in move_lines if x.picking_id and x.picking_id.container_book_id]
            for move in move_lines:
                product_id = move.product_id and move.product_id.id or False
                product_uop = move.product_uop and move.product_uop.id or False
                if product_id and product_uop:
                    line_ids = container_book_line_pool.search(cr, uid, [('booking_id','in',container_booking_ids),('product_id','=',product_id),('product_uop','=',product_uop)])
                    if line_ids:
                        for n in container_book_line_pool.browse(cr, uid, line_ids):
                            packing_type_names.append(n.packing_type and n.packing_type or (n.product_uop and n.product_uop.packing_type and n.product_uop.packing_type.name or ""))

        if packing_type_names:
            packing_type_names = list(set([x for x in packing_type_names if x]))
            return packing_type_names[0]

        return ""

    def _get_totline2(self,invline_obj):
        res=[]
        totline_group={}
        cur_obj = self.pool.get('res.currency')
        for line in invline_obj:
            # key = (product_id, price_unit, account_id, package_type)
            key = (line.product_id.id, \
                line.price_unit, \
                line.account_id, \
                line.move_line_ids and line.move_line_ids[0].product_uop and line.move_line_ids[0].product_uop.packing_type or False, \
                line.invoice_id and line.invoice_id.sale_type and line.invoice_id.sale_type=='export' and \
                (line.move_line_ids and line.move_line_ids[0].sale_line_id  or False) or False)


            if line.invoice_id and line.invoice_id.print_inv_grouping:
                keyx=[]
                for ky in line.invoice_id.print_inv_grouping.split(","):
                    ky=ky.replace("sale_line_id","move_line_ids[0].sale_line_id").replace("product_uop","move_line_ids[0].product_uop").replace("packing_type","move_line_ids[0].product_uop.packing_type").replace("tracking_id","move_line_ids[0].tracking_id and line.move_line_ids[0].tracking_id").replace('move_line_id','move_line_id[0]')
                    try:
                        dumpkey=eval('line.'+str(ky)+".id")
                    except:
                        dumpkey = line.id
                    keyx.append(dumpkey)
                key = tuple(keyx)
            if key not in totline_group:
                totline_group[key] = ["",line.name.replace('\n','<br/>'),"",0,0,0,0,"","","","",0]
            
            totline_group[key][0]=self._get_mark_nos(line)
            totline_group[key][2]=line.uos_id and line.uos_id.name or ''
            totline_group[key][3]+=line.quantity
            totline_group[key][4]=self.get_price_actual(line.invoice_line_tax_id,line.price_unit)
            subtotal = line.quantity*self.get_price_actual(line.invoice_line_tax_id,line.price_unit)
            if line.invoice_id and line.invoice_id.currency_id:
                subtotal = cur_obj.round(self.cr, self.uid, line.invoice_id.currency_id, subtotal)
            totline_group[key][5]+=subtotal
            for z in line.move_line_ids:
                # print z.state,"cnammajjaamaaaaaa"
                if z.state=="done":
                    # totline_group[key][6]+=int(line.move_line_ids and sum([x.product_uop_qty for x in line.move_line_ids]) or 0.0)
                    totline_group[key][6]+=int(sum([z.product_uop_qty ]) or 0.0)
            packing_type = self._get_packing_type(line.move_line_ids)
            totline_group[key][7]= packing_type
            totline_group[key][8]=line.product_id and line.product_id.local_desc
            totline_group[key][9]=line.product_id and line.product_id.export_desc
            totline_group[key][10]=line.move_line_ids and line.move_line_ids.sale_line_id and line.move_line_ids[0].sale_line_id.name
            totline_group[key][11]=line.sequence

        for x in totline_group.keys():
            res.append(totline_group[x])
        # sorting
        res2 = sorted(res, key=lambda k: k[11])
        return res2

    def _call_num2word(self,amount_total,cur):
        amt_id=num2word.num2word_id(amount_total,cur).decode('utf-8')
        return amt_id
        
report_sxw.report_sxw('report.account.print.invoice.form', 'account.invoice', 'reporting_module/commercial_invoice/account_print_invoice_form.mako', parser=account_print_invoice_parser,header=False)
