{
    "name": "Faktur Pajak",
    "version": "1.0",
    "depends": ["sale","report_webkit","account","base","ad_rate_pajak"],
    "author": "Adsoft",
    "category": "Custom Istana/ Surat Pesanan Form",
    "description": """
    This module provide :
    Create Purchase Order Form
    
    Added :
        - Blank Line
    
    Wekit Setting:
        - /usr/local/bin/wkhtmltopdf
    """,
    "init_xml": [],
    'update_xml': [
                   "report/faktur_pajak.xml",
                   "company.xml",
                   "account_move_line_view.xml",
                   "ad_nomor_faktur_pajak_view.xml",
                   "extra_taxes_view.xml",
                   "account_invoice_view.xml",
                   "wizard_generate.xml",
                   "account_tax_view.xml",
                   "account_voucher_view.xml",     
                   "efaktur/efaktur_view.xml",        
                   "qr_code_efaktur/qrcode_tax.xml",
                   "wizard/wizard_faktur_pajak_reconciliation_view.xml",
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
#    'certificate': 'certificate',
}