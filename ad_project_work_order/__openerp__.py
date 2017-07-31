{
	"name": "Bill Work Order on Task",
	"version": "1.0",
	"depends": [
		'base',
		'project',
	],
	"author": "Hendra - hendrasaputra0501@gmail.com",
	"category": "Project Management",
	"description": """
	   Custom module for Project Work Order that given to vendor and creating the Supplier Invoice related to that Work Order on each Task
	""",
	"init_xml": [],
	'update_xml': [
			"project_work_order_view.xml",
			"wizard/wizard_work_order_invoice_view.xml",
	],
	'demo_xml': [],
	'installable': True,
	'active': False,
}
