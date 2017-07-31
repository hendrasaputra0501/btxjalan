{
	"name": "Insurance Bitratex",
	"version": "1.0",
	"depends": ["base","account","ad_account_invoice","ad_invoice_charge"],
	"author": "Hendra - Adsoft",
	"category": "",
	"description": """
	This Module is use to create document for Polis of Marine Cargo Insurance and its claims only on Bitratex.
	Menu that created by this module are :
		* Document Polis
		* Document Claims
	""",
	"init_xml": [ 
		# "data/sequences.xml",
	],
	'update_xml': [
					"insurance_polis_view.xml",
					# "insurance_claims_view.xml",
					"insurance_rate_view.xml",
				   ],
	'demo_xml': [],
	'installable': True,
	'active': False,
	'application':True,
}