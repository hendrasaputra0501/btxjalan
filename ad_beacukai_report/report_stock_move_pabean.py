from openerp import tools
from openerp.osv import fields,osv
from openerp.addons.decimal_precision import decimal_precision as dp

class report_stock_move_pabean(osv.osv):
    _name = "report.stock.move.pabean"
    _description = "Moves Statistics"
    _auto = False
    _columns = {
		'no_pabean': fields.char('No Dokumen Pabean', size=25),
        'sm_id': fields.many2one("stock.move","Move ID"),
        'jns_pabean':fields.selection([(1,'BC 2.3'),(21,'BC 2.7 Masukan'),(22,'BC 2.7 Keluaran'),(3,'BC 4.0'), (4,'BC 4.1'),(5,'BC 3.0'),(6,'BC 2.5'),(71,'BC 2.61'),(72,'BC 2.62')], string="Jenis Dokumen Pabean"),
        'tgl_pabean': fields.date('Tanggal Dokumen Pabean'),
        'date': fields.date('Shipment Date', readonly=True),
        'year': fields.char('Year', size=4, readonly=True),
        'period_id': fields.many2one("account.period","Period",),
        'month':fields.selection([('01','January'), ('02','February'), ('03','March'), ('04','April'),
            ('05','May'), ('06','June'), ('07','July'), ('08','August'), ('09','September'),
            ('10','October'), ('11','November'), ('12','December')], 'Month',readonly=True),
        'partner_id':fields.many2one('res.partner', 'Partner', readonly=True),
        'partner_name': fields.char("Partner Name",size=256,readonly=True),
        'product_uom':fields.many2one('product.uom',"Unit of Measure",readonly=True),
        'product_id':fields.many2one('product.product', 'Product', readonly=True),
        'product_code': fields.char('Product Code',size=128),
        'product_name': fields.char('Product Name',size=128),
        'company_id':fields.many2one('res.company', 'Company', readonly=True),
        'currency_id':fields.many2one('res.currency', 'Currency', readonly=True),
        'price_unit' : fields.float('Price Unit',),
        "subtotal"   : fields.float('Value'),
        'picking_id':fields.many2one('stock.picking', 'Shipment No.', readonly=True),
        'invoice_id':fields.many2one('account.invoice', 'Invoice', readonly=True),
        'product_qty':fields.float('Quantity',readonly=True),
        'type': fields.selection([('out', 'Sending Goods'), ('in', 'Getting Goods'), ('internal', 'Internal'), ('other', 'Others')], 'Shipping Type', required=True, select=True, help="Shipping type specify, goods coming in or going out."),
        'location_id': fields.many2one('stock.location', 'Source Location', readonly=True, select=True, help="Sets a location if you produce at a fixed location. This can be a partner location if you subcontract the manufacturing operations."),
        'location_dest_id': fields.many2one('stock.location', 'Dest. Location', readonly=True, select=True, help="Location where the system will stock the finished products."),
        'state': fields.selection([('draft', 'Draft'), ('waiting', 'Waiting'), ('confirmed', 'Confirmed'), ('assigned', 'Available'), ('done', 'Done'), ('cancel', 'Cancelled')], 'Status', readonly=True, select=True),
        'categ_id': fields.many2one('product.category', 'Product Category', ),
        # 'product_qty_in':fields.integer('In Qty',readonly=True),
        # 'product_qty_out':fields.integer('Out Qty',readonly=True),
        "internal_type":fields.selection([
            ('Finish',"Finished Goods"),
            ('Finish_others',"Finished Good Others"),
            ('Raw Material',"Raw Material"),
            ('Stores',"Stores"),
            ('Waste',"Waste"),
            ('Scrap',"Scrap"),
            ('Fixed','Fixed Assets'),
            ('Packing','Packing Material'),],
            "Internal Type",required=False),
#         'value' : fields.float('Total Value', required=True),
    }

    _order = "date desc, picking_id desc, product_id asc"

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_stock_move_pabean')
        cr.execute("""
            CREATE OR REPLACE view report_stock_move_pabean AS (
                SELECT 
                    sm.id as id,
                    sm.id as sm_id,
                    to_char(date_trunc('day',sm.date), 'YYYY') as year,
                    to_char(date_trunc('day',sm.date), 'MM') as month,
                    to_char(date_trunc('day',sm.date), 'YYYY-MM-DD') as date,
                    bea.registration_no as no_pabean,
                    bea.registration_date as tgl_pabean,
                    case when bea.document_type='23' then 1::integer
                        when bea.document_type='27_in' then 21::integer
                        when bea.document_type='27_out' then 22::integer
                        when bea.document_type='40' then 3::integer
                        when bea.document_type='41' then 4::integer
                        when bea.document_type='30' then 5::integer
                        when bea.document_type='25' then 6::integer
                        when bea.document_type='261' then 71::integer
                        when bea.document_type='262' then 72::integer
                        end as jns_pabean,
                    (select id from account_period where special=False and date_start <= sm.date::timestamp::date and date_stop>=sm.date::timestamp::date) as period_id,
                    sm.partner_id as partner_id,
                    rpt.name as partner_name,
                    sm.product_id as product_id,
                    coalesce(pp.name_template,'No Name Defined') as product_name,
                    coalesce(pp.default_code,'No Code') as product_code,
                    pp.internal_type as internal_type,
                    sm.company_id as company_id,
                    sm.picking_id as picking_id,
                    ail.invoice_id as invoice_id,
                    CASE WHEN sp.type in ('out') THEN
                            res_cur_so.id 
                        WHEN sp.type in ('in') THEN
                            res_cur_po.id
                    END as currency_id,
                    --pu.factor as fact1,pu2.factor as fact2,pu3.factor as fact3,
                    case when sm.invoice_line_id is not NULL THEN
                        (coalesce(ail.price_unit,0.0)*coalesce(pu3.factor,0.0)/pu2.factor) 
                        ELSE
                            CASE WHEN sp.type in ('out') THEN
                                (coalesce(sol.price_unit,0.0)*coalesce(pu5.factor,0.0)/pu.factor)
                            ELSE 
                                (coalesce(pol.price_unit,0.0)*coalesce(pu4.factor,0.0)/pu.factor)
                            END                                
                    END as price_unit,
                    prod.uom_id as product_uom,
                    sp.type as type,
                    sm.location_id as location_id,
                    sm.location_dest_id as location_dest_id,
                    sm.state as state,
                    prod.categ_id as categ_id,
                    CASE WHEN sp.type in ('out') THEN
                        sum(sm.product_qty * pu2.factor/pu.factor )
                         WHEN sp.type in ('in') THEN
                        sum(sm.product_qty * pu2.factor/pu.factor)
                        ELSE 0.0
                        END AS product_qty,
                    CASE WHEN sm.invoice_line_id is not NULL THEN
                        sum(sm.product_qty*pu2.factor/pu.factor*coalesce(ail.price_unit,0.0)*pu3.factor/pu2.factor)
                    ELSE
                        coalesce(
                            CASE WHEN sp.type in ('out') 
                                    THEN sum(sm.product_qty*pu2.factor/pu.factor*coalesce(sol.price_unit,0.0)*pu5.factor/pu.factor)
                                WHEN sp.type in ('in') 
                                    THEN sum(sm.product_qty*pu2.factor/pu.factor*coalesce(pol.price_unit,0.0)*pu4.factor/pu.factor)
                            ELSE 0.0
                                END,0.0) 
                    END AS subtotal
                FROM
                    stock_move sm
                    LEFT JOIN stock_picking sp on sm.picking_id = sp.id 
                    LEFT JOIN account_invoice_line ail on sm.invoice_line_id = ail.id 
                    LEFT JOIN product_product pp on sm.product_id = pp.id
                    LEFT JOIN product_template prod on pp.product_tmpl_id = prod.id
                    LEFT JOIN purchase_order_line pol on sm.purchase_line_id = pol.id
                    LEFT JOIN purchase_order po on pol.order_id = po.id
                    LEFT JOIN sale_order_line sol on sm.sale_line_id = sol.id
                    LEFT JOIN sale_order so on sol.order_id = so.id
                    LEFT JOIN product_uom pu ON (sm.product_uom=pu.id)
                    LEFT JOIN product_uom pu2 ON (prod.uom_id=pu2.id)
                    LEFT JOIN product_uom pu3 ON (ail.uos_id=pu3.id)
                    LEFT JOIN product_uom pu4 ON pol.product_uom=pu4.id
                    LEFT JOIN product_uom pu5 ON sol.product_uom=pu5.id
                    LEFT JOIN product_pricelist so_pricelist on so.pricelist_id = so_pricelist.id
                    LEFT JOIN product_pricelist po_pricelist on po.pricelist_id = po_pricelist.id
                    LEFT JOIN res_currency res_cur_so on so_pricelist.currency_id = res_cur_so.id
                    LEFT JOIN res_currency res_cur_po on po_pricelist.currency_id = res_cur_po.id
                    LEFT JOIN beacukai_stock_picking_rel bspr on sp.id =bspr.stock_picking_id
                    LEFT JOIN beacukai bea on bspr.beacukai_id = bea.id
                    LEFT JOIN res_partner rpt on sp.partner_id=rpt.id
                WHERE pp.bc_remarks='bc'
                GROUP BY
                    sm.id, 
                    sp.type, 
                    sm.date,
                    sm.partner_id,
                    sm.product_id,
                    sm.state,
                    sm.product_uom,
                    sm.product_id,
                    sm.picking_id, 
                    sm.product_qty,
                    sm.company_id,
                    sm.product_qty,
                    sol.price_unit,
                    pol.price_unit,
                    prod.uom_id,
                    prod.categ_id, 
                    sm.location_id,
                    sm.location_dest_id,
                    pp.internal_type,
                    pp.name_template,
                    pp.default_code,
                    res_cur_so.id,
                    res_cur_po.id,
                    ail.price_unit,
                    pu.factor,
                    pu3.factor,
                    pu2.factor,
                    pu4.factor,
                    pu5.factor,
                    bea.registration_no,
                    bea.registration_date,
                    bea.document_type,
                    rpt.name,
                    ail.invoice_id
                ORDER BY
                    sm.date DESC,
                    sm.picking_id DESC,
                    sm.product_id ASC
                       )
        """)

report_stock_move_pabean()