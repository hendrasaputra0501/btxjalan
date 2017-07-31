{
	"name": "Bank Loan",
	"version": "1.0",
	"depends": ["base","account","account_voucher","ad_voucher_extra_writeoff","ad_account_invoice"],
	"author": "Hendra - Adsoft",
	"category": "Accounting and Finance",
	"description": """
	This Module is use to create document for Bank Loan and its reconciliation.
	Menu that created by this module are :
		* Bank Loan
	Reconciliation for will be using Menu :
		* Supplier Payment
	that already exist from module Account Voucher
	""",
	"init_xml": [
		"data/sequences.xml",
	],
	'update_xml': [
					"wizard/import_account_bank_loan_view.xml",
					"bank_loan_view.xml",
					"bank_loan_wkf.xml",
					"interest_rate_view.xml",
					"bank_loan_drawdown_view.xml",
					"account_invoice_view.xml",
				   ],
	'demo_xml': [],
	'installable': True,
	'active': False,
	'application':True,
}