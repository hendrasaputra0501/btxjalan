# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from osv import fields, osv

class accounting_report(osv.osv_memory):
    _inherit = "accounting.report"
    #_inherit = "account.common.report"
    _description = "Accounting Report"

    _columns = {
        'type': fields.selection([('pdf','PDF'),('xls','Excel')], 'Type', required=False),
        'new_report':fields.boolean('Strategic Financial Report'),
    }
    
    _defaults = {
        'type': lambda *a: 'pdf',
    }
        
    def _print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        wizard = self.browse(cr, uid, ids[0], context=context)
        data['form'].update(self.read(cr, uid, ids, ['type', 'date_from_cmp',  'debit_credit', 'date_to_cmp',  'fiscalyear_id_cmp', 'period_from_cmp', 'period_to_cmp',  'filter_cmp', 'account_report_id', 'enable_filter', 'label_filter'], context=context)[0])
        if wizard.type == 'xls':
            final_report = 'account.financial.report.xls'
            if wizard.new_report and wizard.account_report_id.name == 'Profit and Loss':
                final_report ='account.financial.report.new61pnl.xls'
            elif wizard.new_report and wizard.account_report_id.name == 'Balance Sheet':
                final_report ='account.financial.report.new61bs.xls'
        elif wizard.type == 'pdf':
            final_report = 'account.financial.report.pdf'
        #final_report = 'account.financial.report.new61.xls'
        return { 'type': 'ir.actions.report.xml', 'report_name': final_report, 'datas': data, }

accounting_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
