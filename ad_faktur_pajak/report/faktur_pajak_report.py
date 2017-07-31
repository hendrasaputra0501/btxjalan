##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import datetime
from report import report_sxw
from osv import osv,fields
from report.render import render
from ad_num2word_id import num2word
import pooler
from report_tools import pdf_fill,pdf_merge
from tools.translate import _

class faktur(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(faktur, self).__init__(cr, uid, name, context=context)        
        #======================================================================= 
        invoice = self.pool.get('account.invoice').browse(cr, uid, context['active_ids'])[0]
        if invoice.state not in ('proforma2','open','paid') or invoice.type not in ('out_invoice','out_refund'):
            if invoice.type=='out_invoice':
                raise osv.except_osv(_('You can not print Faktur Pajak Form !'), _('Faktur Pajak must be for Customer or State must be Open'))
            elif invoice.type=='out_refund':
                raise osv.except_osv(_('You can not print Nota Retur !'), _('Nota Retur must be for Customer or State must be Open'))
        #=======================================================================
        self.line_no = 0
        self.localcontext.update({
            'time': time,
            'alamat': self.alamat_npwp,
            'convert':self.convert,
            'nourut': self.no_urut,
            'get_ppn': self.get_ppn,
            'line_no':self._line_no,
            'blank_line':self._blank_line,
            'get_internal':self._get_internal,
            'sum_tax':self._sum_tax,
            'get_curr2':self.get_curr,
            'get_invoice':self._get_invoice,
            'get_curr':self._get_used_currency,
            'get_rate_tax': self._get_rate_tax,
            'get_rate_kpmen': self._get_rate_kpmen,
            'get_desc_line' : self._get_desc_line,
            'price_unit' : self._price_unit,
            'get_line_qty_retur':self._get_line_qty_retur,
            'get_line_price_retur':self._get_line_price_retur,
        })
    def _get_line_qty_retur(self,inv_line):
        line1=""
        if inv_line and inv_line.product_id:
            if inv_line.product_id.internal_type in ('Finish','Finish_others'):
                if inv_line.uos_id.id != inv_line.product_id.uom_id.id:
                    line1+=str(self.formatLang(inv_line.quantity,dp="Product Unit of Measure"))+" "+inv_line.uos_id.name+"<br/>"
                    qtykgs = self.pool.get('product.uom')._compute_qty(self.cr, self.uid, inv_line.uos_id.id, inv_line.quantity, inv_line.product_id.uom_id.id)
                    uom_kgs = inv_line.product_id.uom_id.name
                    line1+="("+str(self.formatLang(qtykgs,dp="Product Unit of Measure"))+" "+uom_kgs+")"
                else:
                    line1+=str(self.formatLang(inv_line.quantity,dp="Product Unit of Measure"))+" "+inv_line.uos_id.name+"<br/>"
                    uom_bales = self.pool.get('product.uom').search(self.cr,self.uid,[('name','=','BALES')])
                    try:
                        uom_bales=uom_bales[0]
                    except:
                        uom_bales=uom_bales
                    qtybales = self.pool.get('product.uom')._compute_qty(self.cr, self.uid, inv_line.uos_id.id, inv_line.quantity, uom_bales)
                    line1+="("+str(self.formatLang(qtybales,dp="Product Unit of Measure"))+" BALES)"
            else:
                line1+=str(self.formatLang(inv_line.quantity,dp="Product Unit of Measure"))+" "+inv_line.uos_id.name+"<br/>"
        print "=======qty=======",line1
        return line1

    def _get_line_price_retur(self,inv_line):
        line1=""
        if inv_line:
            if inv_line.uos_id.id != inv_line.product_id.uom_id.id:
                line1+=str(self.formatLang(inv_line.price_subtotal/inv_line.quantity,digits=4))+"<br/>"
                qtykgs = self.pool.get('product.uom')._compute_price(self.cr, self.uid, inv_line.uos_id.id, inv_line.price_subtotal/inv_line.quantity, inv_line.product_id.uom_id.id)
                uom_kgs = inv_line.product_id.uom_id.name
                line1+="("+str(self.formatLang(qtykgs,digits=4))+")"
            else:
                line1+=str(self.formatLang(inv_line.price_subtotal/inv_line.quantity,digits=4))+"<br/>"
                uom_bales = self.pool.get('product.uom').search(self.cr,self.uid,[('name','=','BALES')])
                try:
                    uom_bales=uom_bales[0]
                except:
                    uom_bales=uom_bales
                qtybales = self.pool.get('product.uom')._compute_price(self.cr, self.uid, inv_line.uos_id.id, inv_line.price_subtotal/inv_line.quantity, uom_bales)
                line1+="("+str(self.formatLang(qtybales,digits=4))+")"
        print "=======harga=======",line1
        return line1

    def _get_desc_line(self,inv_line):
        desc = ''
        if inv_line:
            desc += (inv_line.name and (inv_line.name + '\n') or '') 
            desc += (inv_line.quantity and (str(inv_line.quantity) + ' ') or '') 
            desc += (inv_line.uos_id and (inv_line.uos_id.name + ' ') or '') or ''
            desc += (inv_line.invoice_id and inv_line.invoice_id.currency_id and ('- ' + inv_line.invoice_id.currency_id.name + ' ') or '')
            desc += (inv_line.price_unit and (str(self._price_unit(inv_line)) + '\n') or '') 
            
            move_ids = self.pool.get('stock.move').search(self.cr,self.uid,[('invoice_line_id','=',inv_line.id),('product_id','=',inv_line.product_id.id)])
            if move_ids:
                move = self.pool.get('stock.move').browse(self.cr,self.uid,move_ids[0])
                desc += (move.picking_id and ('SJ No: ' + move.picking_id.name + ' ') or '')
                date_delivery = move.picking_id and move.picking_id.date_done!='False' and datetime.datetime.strptime(move.picking_id.date_done,'%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y') or ''
                desc += (date_delivery and ('Date: ' + date_delivery + ' ') or '')
                desc += (move.picking_id and move.picking_id.sale_id and ('Ord.No: ' + move.picking_id.sale_id.name) or '')
        return desc.replace('\n','<br/>')
    
    def _get_rate_tax(self,inv):
        rate = 0.0
        cr = self.cr
        uid = self.uid
        # inv = self.pool.get('account.invoice').browse(self.cr,self.uid,data['id'])        
        if inv.currency_tax_id.name == 'IDR':
            tax_date = inv.tax_date !='False' and inv.tax_date or inv.date_invoice
            # tax_date = inv.date_invoice
            tax_date = self.formatLang(tax_date, date=True)
            tax_rate_ids = self.pool.get('res.currency.tax.rate').search(cr, uid, [('currency_id','=',inv.currency_id.id),('name','<=',datetime.datetime.strptime(tax_date,'%d/%m/%Y').strftime('%Y-%m-%d'))])
            if tax_rate_ids:
                rate = tax_rate_ids and self.pool.get('res.currency.tax.rate').browse(cr,uid,tax_rate_ids)[0].rate or 0.0
        return rate
    
    def _get_rate_kpmen(self,data):
        val = {}
        inv = self.pool.get('account.invoice').browse(self.cr,self.uid,data['id'])
        cr = self.cr 
        uid = self.uid 
        kp_men = ''
        if inv.currency_tax_id.name == 'IDR':
            tax_date = inv.tax_date !='False' and inv.tax_date or inv.date_invoice
            tax_date = self.formatLang(tax_date, date=True)
            tax_rate_ids = self.pool.get('res.currency.tax.rate').search(cr, uid, [('currency_id','=',inv.currency_id.id),('name','<=',datetime.datetime.strptime(tax_date,'%d/%m/%Y').strftime('%Y-%m-%d'))])
            if tax_rate_ids:
                kp_men = (tax_rate_ids and 'Berdasarkan '+self.pool.get('res.currency.tax.rate').browse(cr,uid,tax_rate_ids)[0].kp_men or '')
                kp_men = kp_men + (tax_rate_ids and self.pool.get('res.currency.tax.rate').browse(cr,uid,tax_rate_ids)[0].date_release!='False' and ' Tanggal ' + datetime.datetime.strptime(self.pool.get('res.currency.tax.rate').browse(cr,uid,tax_rate_ids)[0].date_release,'%Y-%m-%d').strftime('%d/%m/%Y') or '')
        return kp_men
  
    def _get_used_currency(self,inv_id):
        invdata=self.pool.get('account.invoice').browse(self.cr,self.uid,inv_id)
        curr=self.pool.get('res.currency')
        if invdata.company_id.currency_id != invdata.currency_id:
            query_rate="select rate from res_currency_rate where name=(select max(name) from res_currency_rate where currency_id="+str(invdata.currency_id.id)+" and name <= '"+str(invdata.date_invoice)+"' ) and currency_id="+str(invdata.currency_id.id)
            self.cr.execute(query_rate)
            rate=map(lambda x: x[0], self.cr.fetchall())
            return curr.round(self.cr,self.uid,invdata.currency_id,1/rate[0])
        else:
            return 1
    
    def _get_curr(self,data):
        ai_data=self.pool.get('account.invoice').browse(self.cr,self.uid,data['id'])
        return ai_data.currency_id.name

    def _price_unit(self,inv_line):
        price = 0.0
        if inv_line:
            if not inv_line.invoice_line_tax_id:
                price=price_unit
            else:
                price=inv_line.price_unit
                for tax in inv_line.invoice_line_tax_id:
                    if tax.price_include:
                        if tax.type=='percent' and not tax.inside_berikat:
                            price=price/(1.0+tax.amount)
        return round(price,4)

    # def _price_unit(self, inv_line):
    #     if not inv_line.invoice_line_tax_id:
    #         return inv_line.price_unit
    #     else:
    #         taxes = self.pool.get('account.tax').compute_all(self.cr, self.uid, inv_line.invoice_line_tax_id, inv_line.price_unit, inv_line.quantity, product=inv_line.product_id, partner=inv_line.invoice_id.partner_id)
    #         return round(taxes['total']/inv_line.quantity,4)
    
    def _sum_tax(self,tax_id):
        taxtotal=0.00
        taxtotal=sum([lt.amount or 0 for lt in tax_id])
        return taxtotal

    def convert(self, amount_total, cur):
        amt_id = num2word.num2word_id(amount_total,"id").decode('utf-8')
        return amt_id
    
    def no_urut(self, list, value):
        return list.index(value) + 1
    
    def get_ppn(self, akun):
        ppn = akun.amount_untaxed*0.1
        return ppn

    def _blank_line(self, nlines, row, type):
        res = ""
        if type=="IDR":
            if row > 15:
                for i in range(nlines+1):
                    res = res + ('<tr class="inv_line"><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
            else:
                for i in range(nlines - row):
                    res = res + ('<tr class="inv_line"><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
        else:
            if row > 15:
                for i in range(nlines+1):
                    res = res + ('<tr class="inv_line"><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')
            else:
                for i in range(nlines - row):
                    res = res + ('<tr class="inv_line"><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>')

        return res

    def _line_no(self):
        self.line_no = self.line_no + 1
        return self.line_no
    
    def _get_internal(self,numb):
        if numb:
            faktur_number_uniq = '00000000'+numb[1:]
            faktur_number_uniq = faktur_number_uniq[-8:]
            return faktur_number_uniq
        else:
            return '.....'
    
    def alamat_npwp(self, partner_id):
        address_id = False
        company_parnter_id=self.pool.get('res.users').browse(self.cr, self.uid, self.uid).company_id.partner_id.id
        if company_parnter_id==partner_id:
            address_id = self.pool.get('res.partner').search(self.cr, self.uid, [('parent_id','=',partner_id),('type','=','contact')])
        
        if not address_id:
            address_id = self.pool.get('res.partner').search(self.cr, self.uid, [('id','=',partner_id)])

        if address_id:
            address = self.pool.get('res.partner').browse(self.cr, self.uid, address_id)[0]
            partner_address = ''
            partner_address += address.street and address.street + '. ' or ''
            partner_address += address.street2 and address.street2 + '\n ' or ''
            partner_address += address.street3 and address.street3 +'. ' or ''
            partner_address += address.city and address.city +' ' or ''
            partner_address += address.zip and address.zip +', ' or ''
            partner_address += address.country_id.name and address.country_id.name or ''
            return  partner_address.replace('\n','<br />').upper()
        else:
            return False
        
    def _get_invoice(self,data):
        inv_id=[data['id']]
        inv_data=self.pool.get('account.invoice').browse(self.cr,self.uid,inv_id)
        if inv_data:
            return inv_data
        else: 
            return False
        
    def get_curr(self,data):
        ai_data=self.pool.get('account.invoice').browse(self.cr,self.uid,data['id'])
        return ai_data.currency_id.name
           
report_sxw.report_sxw('report.faktur.Pajak.valas.form', 'account.invoice', 'addons/ad_faktur_pajak/report/faktur_pajak_valas.mako', parser=faktur,header=False)
report_sxw.report_sxw('report.faktur.Pajak.valas.form.pre', 'account.invoice', 'addons/ad_faktur_pajak/report/faktur_pajak_valas_preprinted.mako', parser=faktur,header=False)
report_sxw.report_sxw('report.faktur.Pajak.valas.form.pre2', 'account.invoice', 'addons/ad_faktur_pajak/report/faktur_pajak_valas_preprinted2.mako', parser=faktur,header=False)

report_sxw.report_sxw('report.faktur.pajak.form', 'account.invoice', 'addons/ad_faktur_pajak/report/faktur_pajak.mako', parser=faktur,header=False)
report_sxw.report_sxw('report.faktur.pajak.form.preprinted', 'account.invoice', 'addons/ad_faktur_pajak/report/faktur_pajak_preprinted.mako', parser=faktur,header=False)
report_sxw.report_sxw('report.faktur.pajak.form.preprinted2', 'account.invoice', 'addons/ad_faktur_pajak/report/faktur_pajak_preprinted2.mako', parser=faktur,header=False)

report_sxw.report_sxw('report.nota.retur', 'account.invoice', 'addons/ad_faktur_pajak/report/nota_retur.mako', parser=faktur,header=False)