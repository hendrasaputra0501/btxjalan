from openerp.osv import fields, osv, orm

class account_move_line(osv.osv):
    """ inherited account.move.line """
    _inherit = 'account.move.line'
    
    def get_amount_residual(self, cr, uid, move_line_id, context=None):
        """
           This function returns the residual amount on a receivable or payable account.move.line.
           By default, it returns an amount in the currency of this journal entry (maybe different
           of the company currency), but if you pass 'residual_in_company_currency' = True in the
           context then the returned amount will be in company currency.
        """
        if context is None:
            context = {}
        if not move_line_id:
            return 0.0, 0.0
        cur_obj = self.pool.get('res.currency')
        move_line = self.browse(cr, uid, move_line_id, context=context)
        if move_line.reconcile_id:
            return 0.0, 0.0

        if move_line.currency_id:
            move_line_total = move_line.amount_currency
            sign = move_line.amount_currency < 0 and -1 or 1
        else:
            move_line_total = move_line.debit - move_line.credit
            sign = (move_line.debit - move_line.credit) < 0 and -1 or 1
        line_total_in_company_currency =  move_line.debit - move_line.credit
        context_unreconciled = context.copy()
        if move_line.reconcile_partial_id:
            for payment_line in move_line.reconcile_partial_id.line_partial_ids:
                if payment_line.id == move_line.id:
                    continue
                    # return 0.0, 0.0
                if payment_line.currency_id and move_line.currency_id and payment_line.currency_id.id == move_line.currency_id.id:
                    move_line_total += payment_line.amount_currency
                else:
                    if move_line.currency_id:
                        context_unreconciled.update({'date': payment_line.date})
                        amount_in_foreign_currency = cur_obj.compute(cr, uid, move_line.company_id.currency_id.id, move_line.currency_id.id, (payment_line.debit - payment_line.credit), round=False, context=context_unreconciled)
                        move_line_total += amount_in_foreign_currency
                    else:
                        move_line_total += (payment_line.debit - payment_line.credit)
                line_total_in_company_currency += (payment_line.debit - payment_line.credit)

        result = move_line_total
        amount_residual_currency =  sign * (move_line.currency_id and self.pool.get('res.currency').round(cr, uid, move_line.currency_id, result) or result)
        amount_residual = sign * line_total_in_company_currency
        return amount_residual_currency, amount_residual

account_move_line()