#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
#
#   Alam Dewata Utama, PT    
#   Copyright (C) 2010-2014 ADSOft (<http://www.adsoft.co.id>). 
#   All Rights Reserved
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

import tools
from osv import osv, fields, expression

class account_account_template(osv.osv):
    """ inherited account.account.template """

    _inherit = "account.account.template"
    _columns = {
        'code2': fields.char('2nd Code', size=64, required=False, select=1),
    }

    def generate_account(self, cr, uid, chart_template_id, tax_template_ref, acc_template_ref, code_digits, company_id, context=None):
        """
        This method for generating accounts from templates.

        :param chart_template_id: id of the chart template chosen in the wizard
        :param tax_template_ref: Taxes templates reference for write taxes_id in account_account.
        :paramacc_template_ref: dictionary with the mappping between the account templates and the real accounts.
        :param code_digits: number of digits got from wizard.multi.charts.accounts, this is use for account code.
        :param company_id: company_id selected from wizard.multi.charts.accounts.
        :returns: return acc_template_ref for reference purpose.
        :rtype: dict
        """
        if context is None:
            context = {}
        obj_acc = self.pool.get('account.account')
        company_name = self.pool.get('res.company').browse(cr, uid, company_id, context=context).name
        template = self.pool.get('account.chart.template').browse(cr, uid, chart_template_id, context=context)
        #deactivate the parent_store functionnality on account_account for rapidity purpose
        ctx = context.copy()
        ctx.update({'defer_parent_store_computation': True})
        level_ref = {}
        children_acc_criteria = [('chart_template_id','=', chart_template_id)]
        if template.account_root_id.id:
            children_acc_criteria = ['|'] + children_acc_criteria + ['&',('parent_id','child_of', [template.account_root_id.id]),('chart_template_id','=', False)]
        children_acc_template = self.search(cr, uid, [('nocreate','!=',True)] + children_acc_criteria, order='id')
        for account_template in self.browse(cr, uid, children_acc_template, context=context):
            # skip the root of COA if it's not the main one
            if (template.account_root_id.id == account_template.id) and template.parent_id:
                continue
            tax_ids = []
            for tax in account_template.tax_ids:
                tax_ids.append(tax_template_ref[tax.id])

            code_main = account_template.code and len(account_template.code) or 0
            code_acc = account_template.code or ''
            code2_acc = account_template.code2 or ''
            if code_main > 0 and code_main <= code_digits and account_template.type != 'view':
                code_acc = str(code_acc) + (str('0'*(code_digits-code_main)))
            parent_id = account_template.parent_id and ((account_template.parent_id.id in acc_template_ref) and acc_template_ref[account_template.parent_id.id]) or False
            #the level as to be given as well at the creation time, because of the defer_parent_store_computation in
            #context. Indeed because of this, the parent_left and parent_right are not computed and thus the child_of
            #operator does not return the expected values, with result of having the level field not computed at all.
            if parent_id:
                level = parent_id in level_ref and level_ref[parent_id] + 1 or obj_acc._get_level(cr, uid, [parent_id], 'level', None, context=context)[parent_id] + 1
            else:
                level = 0
            vals={
                'name': (template.account_root_id.id == account_template.id) and company_name or account_template.name,
                'currency_id': account_template.currency_id and account_template.currency_id.id or False,
                'code': code_acc,
                'code2': code2_acc,
                'type': account_template.type,
                'user_type': account_template.user_type and account_template.user_type.id or False,
                'reconcile': account_template.reconcile,
                'shortcut': account_template.shortcut,
                'note': account_template.note,
                'financial_report_ids': account_template.financial_report_ids and [(6,0,[x.id for x in account_template.financial_report_ids])] or False,
                'parent_id': parent_id,
                'tax_ids': [(6,0,tax_ids)],
                'company_id': company_id,
                'level': level,
            }
            new_account = obj_acc.create(cr, uid, vals, context=ctx)
            acc_template_ref[account_template.id] = new_account
            level_ref[new_account] = level

        #reactivate the parent_store functionnality on account_account
        obj_acc._parent_store_compute(cr)
        return acc_template_ref

account_account_template()

class account_account(osv.osv):
    """ inherited account.account """

    _inherit = "account.account"
    _columns = {
        'code2': fields.char('2nd Code', size=64, required=False, select=1),
    }

    def search(self, cr, uid, args, offset=0, limit=None, order=None,
            context=None, count=False):
        if context is None:
            context = {}
        pos = 0

        while pos < len(args):

            if args[pos][0] == 'code' and args[pos][1] in ('like', 'ilike') and args[pos][2]:
                args[pos] = ('code', '=like', tools.ustr(args[pos][2].replace('%', ''))+'%')
            if args[pos][0] == 'code2' and args[pos][1] in ('like', 'ilike') and args[pos][2]:
                args[pos] = ('code2', '=like', tools.ustr(args[pos][2].replace('%', ''))+'%')
            if args[pos][0] == 'journal_id':
                if not args[pos][2]:
                    del args[pos]
                    continue
                jour = self.pool.get('account.journal').browse(cr, uid, args[pos][2], context=context)
                if (not (jour.account_control_ids or jour.type_control_ids)) or not args[pos][2]:
                    args[pos] = ('type','not in',('consolidation','view'))
                    continue
                ids3 = map(lambda x: x.id, jour.type_control_ids)
                ids1 = super(account_account, self).search(cr, uid, [('user_type', 'in', ids3)])
                ids1 += map(lambda x: x.id, jour.account_control_ids)
                args[pos] = ('id', 'in', ids1)
            pos += 1

        if context and context.has_key('consolidate_children'): #add consolidated children of accounts
            ids = super(account_account, self).search(cr, uid, args, offset, limit,
                order, context=context, count=count)
            for consolidate_child in self.browse(cr, uid, context['account_id'], context=context).child_consol_ids:
                ids.append(consolidate_child.id)
            return ids

        return super(account_account, self).search(cr, uid, args, offset, limit,
                order, context=context, count=count)

    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        args = args[:]
        ids = []
        try:
            if name and str(name).startswith('partner:'):
                part_id = int(name.split(':')[1])
                part = self.pool.get('res.partner').browse(cr, user, part_id, context=context)
                args += [('id', 'in', (part.property_account_payable.id, part.property_account_receivable.id))]
                name = False
            if name and str(name).startswith('type:'):
                type = name.split(':')[1]
                args += [('type', '=', type)]
                name = False
        except:
            pass
        if name:
            if operator not in expression.NEGATIVE_TERM_OPERATORS:
                ids = self.search(cr, user, ['|', ('code', '=like', name+"%"), '|', ('code2', '=like', name+"%"), '|',  ('shortcut', '=', name), ('name', operator, name)]+args, limit=limit)
                if not ids and len(name.split()) >= 2:
                    #Separating code and name of account for searching
                    operand1,operand2 = name.split(' ',1) #name can contain spaces e.g. OpenERP S.A.
                    ids = self.search(cr, user, [('code', operator, operand1), ('name', operator, operand2)]+ args, limit=limit)
            else:
                ids = self.search(cr, user, ['&','!', ('code', '=like', name+"%"), ('name', operator, name)]+args, limit=limit)
                # as negation want to restric, do if already have results
                if ids and len(name.split()) >= 2:
                    operand1,operand2 = name.split(' ',1) #name can contain spaces e.g. OpenERP S.A.
                    ids = self.search(cr, user, [('code', operator, operand1), ('name', operator, operand2), ('id', 'in', ids)]+ args, limit=limit)
        else:
            ids = self.search(cr, user, args, context=context, limit=limit)
        return self.name_get(cr, user, ids, context=context)

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
                    ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'code', 'code2'], context=context)
        res = []
        for record in reads:
            name = record['name']
            code2 = record['code2'] and " ["+record['code2']+"]" or ""
            if record['code']:
                name = record['code'] + code2 + ' ' + name
            res.append((record['id'], name))
        return res

account_account()

class account_period(osv.Model):
    _inherit = 'account.period'

    def finds(self, cr, uid, dt=None, exception=True, context=None):
        if context is None: context = {}
        if not dt:
            dt = fields.date.context_today(self,cr,uid,context=context)
        args = [('date_start', '<=' ,dt), ('date_stop', '>=', dt)]
        if not context.get('special',True):
            args.append(('special','=',False))
        if context.get('company_id', False):
            company_id = context['company_id']
        else:
            company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        args.append(('company_id', '=', company_id))
        ids = self.search(cr, uid, args, context=context)
        if not ids:
            if exception:
                raise osv.except_osv(_('Error!'), _('There is no fiscal year defined for this date.\nPlease create one from the configuration of the accounting menu.'))
            else:
                return []
        return ids

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: