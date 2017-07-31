from openerp.osv import fields,osv
import time
from tools.translate import _

class purchase_internal(osv.Model):
    _name = "purchase.internal"
    _columns = {
        "name"              : fields.char("Number",size=64,required=True),
        "partner_id"        : fields.many2one("res.partner","Origin Partner",required=True),
        "order_date"        : fields.date("Order Date",required=True),
        "effective_date"    : fields.date("Effective Date",required=True),
        "origin_order_id"   : fields.many2one("purchase.order","Origin Document"),
        "order_line"        : fields.one2many("purchase.internal.line","order_id","Order Line"),
        "shop_id"           : fields.many2one("sale.shop","Shop Location",required=True),
        "dest_id"           : fields.many2one("stock.location","Destination"),
        "picking_ids"       : fields.one2many("stock.picking","purchase_internal_id","Incoming Shipment"),
        "journal_id"        : fields.many2one('account.journal',"Journal"),
        "move_id"           : fields.many2one("account.move","Move Entry"),
        "incoming_id"       : fields.many2one("stock.picking","Incoming"),
        "picking_id"        : fields.many2one("stock.picking","Internal Move"),
        "state"             : fields.selection([('draft','Draft'),('delivery',"Waiting for Delivery"),("done","Done"),("cancel","Cancelled")],"State",required=True)
        }
    
    _defaults = {
        "name" : lambda *a:"/DRAFT",
        "order_date": lambda *a:time.strftime("%Y-%m-%d"),
        "state": lambda *a :"draft"
                 }
    
    def onchange_origin_order(self,cr,uid,ids,origin_order_id,context=None):
        if not context:context={}
        val={}
        if origin_order_id:
            purchase = self.pool.get('purchase.order').browse(cr,uid,origin_order_id,context)
            print "========================"
            order = {
                     'order_date'   :purchase.date_order,
                     #'shop_id'      :sale.shop_id and sale.shop_id.id or False,
                     #'dest_id'      :purchase.shop_id and sale.shop_id.warehouse_id.lot_stock_id and sale.shop_id.warehouse_id.lot_stock_id.id or False,
                     'order_line'   :[],
                     }
            line = [{
                "name"              : oline.name,
                "product_id"        : oline.product_id and oline.product_id.id or False,
                "product_uom_id"    : oline.product_uom and oline.product_uom.id or False,
                #"product_uos_id"    : oline.product_uos and oline.product_uos.id or False,
                "product_qty"       : oline.product_uom and oline.product_qty or 0.0,
                #"product_uos_qty"   : oline.product_uos and oline.product_uos_qty or 0.0,
                "price_unit"        : oline.price_unit or 0.0,
                "amount_total"      : oline.price_subtotal or 0.0,
                "order_line_id"     : oline.id or False
                } for oline in purchase.order_line]
            order.update({'order_line':line})
            val.update({'value':order})
        return val
    
    def action_confirm(self,cr,uid,ids,context=None):
        if not context:context={}
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        move_ids = []
        for order in self.browse(cr,uid,ids):

            total = 0.0
            for line in order.order_line:
                total += line.amount_total
            period =self.pool.get('account.period').find(cr,uid,dt=order.effective_date and order.effective_date or time.strftime('%Y-%m-%d'))
            move = {
                'name': order.name,
                'journal_id': order.journal_id and order.journal_id.id,
                'date': order.effective_date or time.strftime('%Y-%m-%d'),
                'period_id': period and period[0] or False,
            }
            move_id = move_pool.create(cr,uid,move,context)
            move_line_debit = {
                'name': order.name or '/',
                'debit': total,
                'credit': 0.0,
                'account_id': order.journal_id.default_debit_account_id and order.journal_id.default_debit_account_id.id or False,
                'move_id': move_id,
                'journal_id': order.journal_id and order.journal_id.id or False,
                'period_id': period and period[0] or False,
                'partner_id': order.partner_id and order.partner_id.id or False,
                #'currency_id': order.journal_id.company_id.currency_id.id,
                #'amount_currency': company_currency <> current_currency and sign * advance.total_amount or 0.0,
                'date': order.effective_date or time.strftime('%Y-%m-%d'),
                }
            move_line_credit = {
                'name': order.name or '/',
                'debit': 0.0,
                'credit': total,
                'account_id': order.journal_id.default_credit_account_id and order.journal_id.default_credit_account_id.id or False,
                'move_id': move_id,
                'journal_id': order.journal_id and order.journal_id.id or False,
                'period_id': period and period[0] or False,
                'partner_id': order.partner_id and order.partner_id.id or False,
                #'currency_id': order.journal_id.company_id.currency_id.id,
                #'amount_currency': company_currency <> current_currency and sign * advance.total_amount or 0.0,
                'date': order.effective_date or time.strftime('%Y-%m-%d'),
                }
            for mvline in [move_line_debit,move_line_credit]:
                move_line_pool.create(cr,uid,mvline,context)
            move_ids.append(move_id)
            if order.incoming_id and not order.picking_id:
                picking_id = self.pool.get('stock.picking').copy(cr,uid,order.incoming_id.id,context)

                if picking_id:
                    picking = self.pool.get('stock.picking').browse(cr,uid,picking_id,context)
                    seq_obj_name = 'stock.picking'
                    default = {
                        'name'          : self.pool.get('ir.sequence').get(cr, uid, seq_obj_name),
                        'origin'        : '',
                        'backorder_id'  : False,
                        'type'          : 'internal',
                        'purchase_id'   : False,
                        'invoice_state' : 'none',
                        'purchase_internal_id': order.id or False,
                        }
                    lines={}
                    for line in picking.move_lines:
                        lines[line.id]={
                            'location_id':line.location_dest_id and line.location_dest_id.id or False,
                            'location_dest_id':order.dest_id and order.dest_id.id or False,
                            }
                    for mv_line in lines.keys():
                        self.pool.get('stock.move').write(cr,uid,mv_line,lines[mv_line],context)

                    self.pool.get('stock.picking').write(cr,uid,picking_id,default,context)

            order.write({'move_id':move_id,'picking_id':picking_id,'state':'delivery'})
        move_pool.post(cr,uid,move_ids,context)

        return True

    def action_cancel(self,cr,uid,ids,context=None):
        if not context:
            context={}
        move_pool=self.pool.get('account.move')
        picking_pool=self.pool.get('stock.picking')
        for order in self.browse(cr,uid,ids,context):
            if order.move_id:
                move_pool.button_cancel(cr,uid,[order.move_id.id],context)
                move_pool.unlink(cr,uid,[order.move_id.id],context)
            if order.picking_id:
                if order.picking_id.state == 'draft':
                    picking_pool.unlink(cr,uid,[order.picking_id.id],context)
                elif order.picking_id.state in 'cancel':
                    order.write({'picking_id':False})
                elif order.picking.state == 'done':
                    raise osv.except_osv(_('Error'), _("There is a finished internal move document ('%s') created,\n you have to reverse transfer this process first") %(order.picking_id and order.picking_id.name))
            order.write({'state':'cancel'})
        return True

    def action_draft(self,cr,uid,ids,context=None):
        return self.write(cr,uid,ids,{'state':'draft'},context)

class purchase_internal_line(osv.Model):
    _name = "purchase.internal.line"
    _columns = {
        "name"              : fields.char("Description",size=64,required=True),
        "order_id"          : fields.many2one("purchase.internal","Purchase Internal",required=True,ondelete="cascade"),
        "product_id"        : fields.many2one("product.product","Product"),
        "product_uom_id"    : fields.many2one("product.uom","Unit of Measure",required=True),
        #"product_uos_id"    : fields.many2one("product.uom","Unit of Sale",required=False),
        "product_qty"       : fields.float("Quantity",required=True),
        #"product_uos_qty"   : fields.float("UoS Qty"),
        "price_unit"        : fields.float("Price Unit",required=True),
        "amount_total"      : fields.float("Amount Total"),
        "order_line_id"     : fields.many2one('purchase.order.line',"Purchase Order Line",required=True),
                }
    _defaults = {
        "name": lambda *a:"/",
                 }
    
class stock_picking(osv.Model):
    _inherit ="stock.picking"
    _columns = {
        "purchase_internal_id"  : fields.many2one("purchase.internal","Purchase Internal"),
                }