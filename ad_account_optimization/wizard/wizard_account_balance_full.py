# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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
        #print 'Exception in create report:',e
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
    <form string="Full Account Balance">
        <field name="company_id"/>
        <newline/>
        <group colspan="4">
        <separator string="Accounts to include" colspan="4"/>
            <field name="account_list" nolabel="1" colspan="4" domain="[('company_id','=',company_id)]" help="asdfasdfasdfasdf"/>
            <field name="display_account" required="True"/>
            <field name="display_account_level" required="True" />
        </group>
        <group colspan="4">
            <separator string="Period" colspan="4"/>
            <field name="fiscalyear"/>
            <newline/>
            <field name="state" required="True"/>
            <newline/>
            <group attrs="{'invisible':[('state','=','none')]}" colspan="4">
                <group attrs="{'invisible':[('state','=','byperiod')]}" colspan="4">
                    <separator string="Date Filter" colspan="4"/>
                    <field name="date_from"/>
                    <field name="date_to"/>
                </group>
                <group attrs="{'invisible':[('state','=','bydate')]}" colspan="4">
                    <separator string="Filter on Periods" colspan="4"/>
                    <field name="periods" colspan="4" nolabel="1" domain="[('fiscalyear_id','=',fiscalyear)]"/>
                </group>
            </group>
        </group>
    </form>'''

    def _get_defaults(self, cr, uid, data, context={}):
        user = pooler.get_pool(cr.dbname).get('res.users').browse(cr, uid, uid, context=context)
        if user.company_id:
           company_id = user.company_id.id
        else:
           company_id = pooler.get_pool(cr.dbname).get('res.company').search(cr, uid, [('parent_id', '=', False)])[0]
        data['form']['company_id'] = company_id
        fiscalyear_obj = pooler.get_pool(cr.dbname).get('account.fiscalyear')
        data['form']['fiscalyear'] = fiscalyear_obj.find(cr, uid)
        
        if (data['model'] == 'account.account'):
            data['form']['account_list'] = data['ids']
        data['form']['context'] = context
        return data['form']

    def _check_state(self, cr, uid, data, context):
        #print "xxxxxxxxx",data['form']['amount_currency']
        if data['form']['state'] == 'bydate':
           self._check_date(cr, uid, data, context)
        #print "ttttttttt",data['form']   
        return data['form']
    
    """def _check_report(self):
        if data['form']['amount_currency'] == 0:
            return 'account.balance.full'
        else:
            return 'account.balance.full.currency'"""
        #return data['form']
    
    def _get_email_defaults(self, cr, uid, data, context):
        p = pooler.get_pool(cr.dbname)
        user = p.get('res.users').browse(cr, uid, uid, context)
        
        if user.company_id:
           company_id = user.company_id.id
        else:
           company_id = pooler.get_pool(cr.dbname).get('res.company').search(cr, uid, [('parent_id', '=', False)])[0]
        
        fiscalyear = p.get('account.fiscalyear').browse(cr, uid, uid, context)

        res_ids = p.get('ir.model').search(cr, uid, [('model', '=', 'account.account')], context=None)
        report_name = "account.balance.full"
        file_name = user.company_id.name.replace(' ','_')+'_'+_('account_balance_report')
        report = create_report(cr, uid, res_ids, data, report_name, file_name)[1] or 'attachement'

        to = ""
        subject = "ACCOUNT BALANCE REPORT, %s, Date from: %s to %s" % \
            (fiscalyear.name or fiscalyear.code, data['form']['date_from'], data['form']['date_to'])
        text = 'Dear ...........,\n\n' + \
                'Herewith I enclose the ' + subject + \
                '\n' + \
                '---------\n' + \
                user.signature

        return {'attachment_file': report, 'to': to, 'subject': subject, 'text': text}
        
    def _send_mails(self, cr, uid, data, context):
        
        import re
#        p = pooler.get_pool(cr.dbname)
#    
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
#
#        return {'email_sent': nbr}
        
        # Create report to send as file attachments
        """
        # Add a partner event
        docs = p.get(data['model']).browse(cr, uid, data['ids'], context)
        partner_id = docs[0].partner_id.id
        c_id = p.get('res.partner.canal').search(cr ,uid, [('name','ilike','EMAIL'),('active','=',True)])
        c_id = c_id and c_id[0] or False
        p.get('res.partner.event').create(cr, uid,
                {'name': _('Email sent through sale order wizard'),
                 'partner_id': partner_id,
                 'description': _('To: ').encode('utf-8') + data['form']['to'] +
                                _('\n\nSubject: ').encode('utf-8') + data['form']['subject'] +
                                _('\n\nText:\n').encode('utf-8') + data['form']['text'],
                 'document': data['model']+','+str(docs[0].id),
                 'canal_id': c_id,
                 'user_id': uid, })
        return {'email_sent': nbr}"""
    
    options_fields = {
        'company_id': {'string': 'Company', 'type': 'many2one', 'relation': 'res.company', 'required': True},
        'account_list': {'string': 'Root accounts', 'type':'many2many', 'relation':'account.account', 'required':True ,'domain':[]},
        'state':{
            'string':"Date/Period Filter",
            'type':'selection',
            'selection':[('bydate','By Date'),('byperiod','By Period'),('all','By Date and Period'),('none','No Filter')],
            'default': lambda *a:'none'
        },
        'fiscalyear': {
            'string':'Fiscal year',
            'type':'many2one',
            'relation':'account.fiscalyear',
            'help':'Keep empty to use all open fiscal years to compute the balance'
        },
        'amount_currency':{'string':"With Currency", 'type':'boolean'},
        'periods': {'string': 'Periods', 'type': 'many2many', 'relation': 'account.period', 'help': 'All periods in the fiscal year if empty'},
        'display_account':{'string':"Display accounts ", 'type':'selection', 'selection':[('bal_all','All'),('bal_solde', 'With balance'),('bal_mouvement','With movements')]},
        'display_account_level':{'string':"Up to level", 'type':'integer', 'default': lambda *a: 0, 'help': 'Display accounts up to this level (0 to show all)'},
        'date_from': {'string':"Start date", 'type':'date', 'required':True, 'default': lambda *a: time.strftime('%Y-01-01')},
        'date_to': {'string':"End date", 'type':'date', 'required':True, 'default': lambda *a: time.strftime('%Y-%m-%d')},
    }
    report_send_fields = { 
        'mail_service_id': {'string': 'Select Mail Service', 'type': 'many2one',
                            'relation': 'dm.mail_service',},
        } 

    states = { 
        'init': {
            'actions': [_get_defaults],
            'result': {'type': 'form', 'arch': options_form, 
                       'fields': options_fields,
                'state': [('end', 'Cancel', 'gtk-cancel'),
                          ('print2pdf', 'Print', 'gtk-print'),
                          ('print2excel', 'Excel', 'gtk-convert'),
#                          ('send_report', 'Email', 'gtk-go-forward'),
                          ]}
            },
        'print2pdf': {#'account.balance.full'
            'actions': [_check_state],
            'result': {'type': 'print', 'report': 'account.balance.full', 'state': 'end'}
            },
        'print2excel': {
            'actions': [],
            'result': {'type': 'print', 'report': 'account.balance.full.xls', 'state': 'end'}
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

wizard_report('ad.account.balance.full.report')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
