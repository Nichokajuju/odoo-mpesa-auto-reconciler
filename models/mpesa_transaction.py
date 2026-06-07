from odoo import models, fields, api
from odoo.exceptions import UserError


class MpesaTransaction(models.Model):
    _name = 'mpesa.transaction'
    _description = 'M-Pesa Transaction'
    _rec_name = 'transaction_id'
    _order = 'transaction_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    transaction_id = fields.Char(
        string='Transaction ID',
        required=True,
        copy=False,
        index=True,
        tracking=True,
    )
    transaction_date = fields.Datetime(
        string='Transaction Date',
        default=fields.Datetime.now,
    )
    amount = fields.Float(
        string='Amount',
        required=True,
        digits=(16, 2),
    )
    phone_number = fields.Char(
        string='Phone Number',
    )
    sender_name = fields.Char(
        string='Sender Name',
    )
    reference = fields.Char(
        string='Reference',
    )
    transaction_type = fields.Selection([
        ('paybill', 'Paybill'),
        ('till', 'Till'),
        ('stk_push', 'STK Push'),
    ], string='Transaction Type', default='paybill')

    state = fields.Selection([
        ('pending', 'Pending'),
        ('matched', 'Matched'),
        ('reconciled', 'Reconciled'),
        ('failed', 'Failed'),
    ], string='State', default='pending', index=True, tracking=True)

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        index=True,
        tracking=True,
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        domain=[('move_type', '=', 'out_invoice')],
        tracking=True,
    )
    payment_id = fields.Many2one(
        'account.payment',
        string='Payment',
        readonly=True,
    )
    notes = fields.Text(
        string='Notes',
    )

    def action_match_invoice(self):
        for rec in self:
            if rec.state == 'reconciled':
                raise UserError('Transaction %s is already reconciled.' % rec.transaction_id)

            invoice = None
            domain_base = [
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'not in', ['paid', 'in_payment']),
            ]

            if rec.reference:
                invoice = self.env['account.move'].search(
                    domain_base + [('name', 'ilike', rec.reference)],
                    limit=1
                )

            if not invoice:
                invoice = self.env['account.move'].search(
                    domain_base + [('amount_total', '=', rec.amount)],
                    limit=1
                )

            if invoice:
                rec.invoice_id = invoice.id
                rec.partner_id = invoice.partner_id.id
                rec.state = 'matched'
                rec.notes = 'Matched to invoice %s' % invoice.name
            else:
                rec.state = 'failed'
                rec.notes = 'No matching invoice found for amount %s or reference %s' % (
                    rec.amount, rec.reference
                )

    def action_reconcile(self):
        for rec in self:
            if rec.state != 'matched':
                raise UserError(
                    'Transaction %s must be matched before reconciling.' % rec.transaction_id
                )
            if not rec.invoice_id:
                raise UserError(
                    'Transaction %s has no linked invoice.' % rec.transaction_id
                )
            if not rec.partner_id:
                raise UserError(
                    'Transaction %s has no linked customer.' % rec.transaction_id
                )

            invoice = rec.invoice_id

            journal = self.env['account.journal'].search([
                ('name', 'ilike', 'mpesa'),
                ('type', '=', 'bank'),
            ], limit=1)
            if not journal:
                journal = self.env['account.journal'].search([
                    ('type', '=', 'bank'),
                ], limit=1)
            if not journal:
                raise UserError(
                    'No bank journal found. Please create an M-Pesa journal in Accounting > Configuration > Journals.'
                )

            payment = self.env['account.payment'].create({
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': rec.partner_id.id,
                'amount': rec.amount,
                'currency_id': invoice.currency_id.id,
                'journal_id': journal.id,
                'date': rec.transaction_date or fields.Date.today(),
                'memo': 'M-Pesa: %s' % rec.transaction_id,
            })

            payment.action_post()

            invoice_lines = invoice.line_ids.filtered(
                lambda l: l.account_id.account_type == 'asset_receivable'
                and not l.reconciled
            )
            payment_lines = payment.move_id.line_ids.filtered(
                lambda l: l.account_id.account_type == 'asset_receivable'
                and not l.reconciled
            )

            if invoice_lines and payment_lines:
                (invoice_lines + payment_lines).reconcile()
            else:
                raise UserError(
                    'Could not find receivable lines to reconcile for transaction %s.' % rec.transaction_id
                )

            rec.payment_id = payment.id
            rec.state = 'reconciled'
            rec.notes = 'Reconciled. Payment: %s' % payment.name

    def action_reset_to_pending(self):
        for rec in self:
            if rec.state == 'reconciled':
                raise UserError('Cannot reset a reconciled transaction.')
            rec.state = 'pending'
            rec.invoice_id = False
            rec.partner_id = False
            rec.notes = 'Reset to pending.'

    def action_batch_match(self):
        """Match all selected pending transactions to invoices."""
        pending = self.filtered(lambda r: r.state == 'pending')
        if not pending:
            raise UserError('No pending transactions selected.')
        pending.action_match_invoice()
        matched = self.filtered(lambda r: r.state == 'matched')
        failed = self.filtered(lambda r: r.state == 'failed')
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Batch Match Complete',
                'message': '%d matched, %d failed.' % (len(matched), len(failed)),
                'type': 'success' if matched else 'warning',
                'sticky': False,
            }
        }

    def action_batch_reconcile(self):
        """Reconcile all selected matched transactions."""
        matched = self.filtered(lambda r: r.state == 'matched')
        if not matched:
            raise UserError('No matched transactions selected. Run Match Invoice first.')

        success = 0
        failed_list = []

        for rec in matched:
            try:
                rec.action_reconcile()
                success += 1
            except Exception as e:
                failed_list.append('%s: %s' % (rec.transaction_id, str(e)))

        message = '%d reconciled successfully.' % success
        if failed_list:
            message += ' %d failed: %s' % (len(failed_list), ', '.join(failed_list))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Batch Reconcile Complete',
                'message': message,
                'type': 'success' if not failed_list else 'warning',
                'sticky': True,
            }
        }
