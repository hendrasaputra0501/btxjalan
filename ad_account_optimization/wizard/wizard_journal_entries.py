# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

import wizard
import pooler
import time
from tools.translate import _
from osv import fields,osv
import netsvc
from tools.misc import UpdateableStr, UpdateableDict

def create_report(cr, uid, res_ids, data, report_name=False, file_name=False):

    if not report_name or not res_ids:
        return (False, Exception('Report name and Resources ids are required !!!'))
    try:
        ret_file_name = '/tmp/'+file_name+'.pdf'
        service = netsvc.LocalService("report."+report_name)
        #(result, format) = service.create(cr, uid, res_ids, {'model': 'account.account'}, {})
        (result, format) = service.create(cr, uid, res_ids, data, {})
        fp = open(ret_file_name, 'wb+')
        fp.write(result)
        fp.close()
    except Exception,e:
        print 'Exception in create report:',e
        return (False, str(e))
    return (True, ret_file_name)

class wizard_report(wizard.interface):

    email_send_form = '''<?xml version="1.0" encoding="utf-8"?>
    <form string="Send Report via Email" height="500" widht="400">
        <field name="attachment_file"/>
        <newline/>
        <field name="alternate_attached"/>
        <newline/>
        <field name="to"/>
        <newline/>
        <field name="subject"/>
        <newline/>
        <separator string="Message:" colspan="4"/>
        <field name="text" nolabel="1" colspan="4"/>
    </form>'''
    
    email_send_fields = {
        'attachment_file': {'string':"Attachment", 'type':'char', 'size':512, 'required':True},
        'alternate_attached':{'string':"Choose from Computer", 'type':'binary'},
        'to': {'string':"To", 'type':'char', 'size':512, 'required':True},
        'subject': {'string':'Subject', 'type':'char', 'size': 512, 'required':True},
        'text': {'string':'Message', 'type':'text_tag', 'required':True}
    }
    
    email_done_form = '''<?xml version="1.0" encoding="utf-8"?>
    <form string="Send sale order/s by Email">
        <field name="email_sent"/>
    </form>'''
    
    email_done_fields = {
        'email_sent': {'string':'Quantity of Emails sent', 'type':'integer', 'readonly': True},
    }
    
    options_form = '''<?xml version="1.0"?>
    <form string="Print Journal" >
        <field name="journal_ids" width="300" height="500"/>
        <field name="period_ids"/>
        <field name="sort_selection"/>
    </form>'''

    def _get_defaults(self, cr, uid, data, context):
        fiscalyear_obj = pooler.get_pool(cr.dbname).get('account.fiscalyear')
        period_obj = pooler.get_pool(cr.dbname).get('account.period')
        journal_obj = pooler.get_pool(cr.dbname).get('account.journal')
        data['form']['period_ids'] = period_obj.search(cr, uid, [('fiscalyear_id','=',fiscalyear_obj.find(cr, uid))])
        data['form']['journal_ids'] = journal_obj.search(cr, uid, [])
        return data['form']

    def _check_data(self, cr, uid, data, *args):
        period_id = data['form']['period_ids'][0][2]
        journal_id = data['form']['journal_ids'][0][2]
        if type(period_id)==type([]):

            ids_final = []
            for journal in journal_id:
                for period in period_id:
                    ids_journal_period = pooler.get_pool(cr.dbname).get('account.journal.period').search(cr,uid, [('journal_id','=',journal),('period_id','=',period)])

                    if ids_journal_period:
                        ids_final.append(ids_journal_period)

            if not ids_final:
                raise wizard.except_wizard(_('No Data Available'), _('No records found for your selection!'))
        return data['form']


    """def _check_landcape(self, cr, uid, data, context):
        if data['form']['landscape']==True:
            final_report = 'account.print.ad.journal.entriesh'
           
        else:
            final_report = 'account.print.ad.journal.entries'
           

        return {
            'type': 'ir.actions.report.xml',
            'report_name': final_report,
            'datas': data,
        }"""


            
    def _get_email_defaults(self, cr, uid, data, context):
        p = pooler.get_pool(cr.dbname)
        user = p.get('res.users').browse(cr, uid, uid, context)
        
        if user.company_id:
           company_id = user.company_id.id
        else:
           company_id = pooler.get_pool(cr.dbname).get('res.company').search(cr, uid, [('parent_id', '=', False)])[0]
        
        period_ids = p.get('account.period').browse(cr, uid, uid, context)

        res_ids = p.get('ir.model').search(cr, uid, [('model', '=', 'account.journal.period')], context=None)
        report_name = "account.print.ad.journal.entries"
        file_name = user.company_id.name.replace(' ','_')+'_'+_('journal_entries_report')
        report = create_report(cr, uid, res_ids, data, report_name, file_name)[1] or 'attachement'

        to = ""
        subject = "JOURNAL by ENTRIES REPORT, %s,  %s" % \
            (period_ids.name or period_ids.code, data['form']['journal_ids'])
        text = 'Dear ...........,\n\n' + \
                'Herewith I enclose the ' + subject + \
                '\n' + \
                '---------\n' + \
                user.signature

        return {'attachment_file': report, 'to': to, 'subject': subject, 'text': text}
        
    def _send_mails(self, cr, uid, data, context):
        
        import re
        p = pooler.get_pool(cr.dbname)
    
#        user = p.get('res.users').browse(cr, uid, uid, context)
#        file_name = user.company_id.name.replace(' ','_')+'_'+_('Sale_Order')
#        
#        default_smtpserver_id = p.get('email.smtpclient').search(cr, uid, [('users_id','=',uid), ('pstate','=','running')], context=None)
#        if default_smtpserver_id:
#            default_smtpserver_id = default_smtpserver_id[0]
#        else:
#            raise osv.except_osv(_('Error'), 
#                                 _('Can\'t send email, please check whether SMTP client has been defined and you have permission to access!'))
#        
#        attachments = data['form']['attachment_file']
#        attachments = [attachments] or []
        nbr = 0
#        for email in data['form']['to'].split(','):
#            state = p.get('email.smtpclient').send_email(cr, uid, default_smtpserver_id, email, data['form']['subject'], data['form']['text'], attachments)
#            if not state:
#                raise osv.except_osv(_('Error sending email'), _('Please check the Server Configuration!'))
#            nbr += 1

        return {'email_sent': nbr}
    
    options_fields = {
            'journal_ids': {'string': 'Journal', 'type': 'many2many', 'relation': 'account.journal', 'required': True},
            'period_ids': {'string': 'Period', 'type': 'many2many', 'relation': 'account.period', 'required': True},
            'sort_selection': {
                'string':"Entries Sorted By",
                'type':'selection',
                'selection':[('date','By date'),("to_number(name,'999999999')",'By entry number'),('ref','By reference number')],
                'required':True,
                'default': lambda *a: 'date',
                },
        }
    
    report_send_fields = { 
        'mail_service_id': {'string': 'Select Mail Service', 'type': 'many2one',
                            'relation': 'dm.mail_service',},
        }

    states = { 
        'init': {
            'actions': [_get_defaults],
            'result': {'type': 'form', 'arch': options_form, 'fields': options_fields,
            'state': [('end', 'Cancel', 'gtk-cancel'),
                      ('print2pdf', 'Print', 'gtk-print'),
                      ('print2pdf_landscape', 'Print Landscape', 'gtk-print'),
                      ('print2excel', 'Excel', 'gtk-convert'),
#                      ('send_report', 'Email', 'gtk-go-forward'),
                    ]
                }
            },
        'print2pdf': {
            'actions': [],
            'result': {'type': 'print', 'report': 'account.print.journal.entries', 'state': 'end'}
            },  
        'print2pdf_landscape': {
            'actions': [],
            'result': {'type': 'print', 'report': 'account.print.journal.entriesh', 'state': 'end'}
            },  
         'print2excel': {
            'actions': [],
            'result': {'type': 'print', 'report': 'account.move.line.xls', 'state': 'end'}
            },
         'send_report': {
           'actions': [_get_email_defaults],
            'result': {
                'type': 'form', 
                'arch': email_send_form, 
                'fields': email_send_fields, 
                'state':[('end','Cancel', 'gtk-cancel'), ('send','Send Email', 'gtk-go-forward')]}
            },
         'send': {
            'actions': [_send_mails],
            'result': {'type': 'form', 'arch': email_done_form, 'fields': email_done_fields, 'state': [('end', 'End')] }
            },
        }
                          
 
wizard_report('ad.account.journal.entries.report')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

