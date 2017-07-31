{
	'name': 'Material Requisition',
	'version': '7.0',
	'category': 'Procurement/Material Request',
	'description': """
	 - Material Request
	 - Create Internal Move Record 
	 - Approval Budget & Non Budget  
	""",
	'author': 'Dedi - ADSOFT',
	'depends': ['base','stock','product','purchase_requisition',"purchase","procurement","account_budget","ad_product_info_bitratex","ad_container_booking"],
	'data':[
	],
	'update_xml': [
		"wizard/material_request_collecting.xml",
		"wizard/mr_line_add_to_existion_pr.xml",
		"wizard/issue_material_request_view.xml",
		"security/access_security.xml",
		"hr_department_view.xml",
		"sequence/sequence.xml",
		"material_requisition_view.xml",
		"material_requisition_workflow.xml",
		"purchase_requisition_view.xml",
		"purchase_order_view.xml",
		"purchase_requisition_workflow.xml",
		"product_view.xml",
		"analytic_account_view.xml",
		"report/item_request_form_view.xml",
		"report/supplier_comparison_approval_view.xml",
		"stock_move_view.xml",
		"stock_picking_view.xml",
		#"stock_view.xml",
		# "product_view.xml",
		# "material_req_view.xml",
		# "material_sequence.xml",
		# "workflow_pr.xml",
		# "res_users_view.xml",
		# "email_scheduler.xml",
		# "po_workflow.xml",
		# "purchase_requisition_sequence.xml"
	],
	'test': [],	
	'installable': True,
	'active': False,
	'certificate':''   
}
