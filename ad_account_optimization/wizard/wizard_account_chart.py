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
    <form string="Send Report via Email">
        <field name="attachment_file"/>
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
    <form string="Select parent account" height="200">
    <field name="account" colspan="4"/>
    </form>'''    
    
   
    def _get_email_defaults(self, cr, uid, data, context):
        p = pooler.get_pool(cr.dbname)
        user = p.get('res.users').browse(cr, uid, uid, context)
        
        if user.company_id:
           company_id = user.company_id.id
        else:
           company_id = pooler.get_pool(cr.dbname).get('res.company').search(cr, uid, [('parent_id', '=', False)])[0]
        
        account = p.get('account.account').browse(cr, uid, uid, context)

        res_ids = p.get('ir.model').search(cr, uid, [('model', '=', 'account.account')], context=None)
        report_name = "ad.account.account.chart.report"
        file_name = user.company_id.name.replace(' ','_')+'_'+_('chart_of_account')
        report = create_report(cr, uid, res_ids, data, report_name, file_name)[1] or 'attachement'

        to = ""
        subject = "CHART OF ACCOUNT , %s, " % \
            (account.name or account.code, )
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
#        nbr = 0
#        for email in data['form']['to'].split(','):
#            state = p.get('email.smtpclient').send_email(cr, uid, default_smtpserver_id, email, data['form']['subject'], data['form']['text'], attachments)
#            if not state:
#                raise osv.except_osv(_('Error sending email'), _('Please check the Server Configuration!'))
#            nbr += 1

        return {'email_sent': nbr}
    
    

    options_fields = {
     'account': {'string':'Account', 'type':'many2one', 'relation':'account.account', 'required':True},
    }


    report_send_fields = { 
        'mail_service_id': {'string': 'Select Mail Service', 'type': 'many2one',
                            'relation': 'dm.mail_service',},
        }
   


    states = {
        
        'init': {
            'actions': [],
            'result': {'type': 'form', 'arch': options_form, 'fields': options_fields,
                'state': [('end', 'Cancel', 'gtk-cancel'),
                          ('report', 'Print', 'gtk-print'),
                          ('print2excel', 'Excel', 'gtk-convert'),
#                          ('send_report', 'Email', 'gtk-go-forward'),
                          ]}
            #'result': {'type':'form', 'arch':account_form,'fields':account_fields, 'state':[('end','Cancel'),('report','Print')]}
        },
        'report': {
            'actions': [],
            'result': {'type':'print', 'report':'account.chart.report', 'state':'end'}
        },
        'print2excel': {
            'actions': [],
            'result': {'type': 'print', 'report': 'account.chart.xls', 'state': 'end'}
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
wizard_report('ad.account.account.chart.report')


