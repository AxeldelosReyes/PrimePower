from odoo import models, fields, api, _

class CreditLimitAlertResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    credit_limit = fields.Monetary('Limite de credito')
    credit_available = fields.Monetary('Credito disponible', compute='_compute_amount_credit_available')

    @api.depends('credit_limit','credit_available','credit')
    def _compute_amount_credit_available(self):

        self.credit_available = self.credit_limit - self.credit

        pass

    current_user_approval = fields.Boolean('is current user approval', compute='_get_current_user', store=False)

    def _get_current_user(self):
        for record in self:
            record.current_user_approval = record.env.user.has_group('credit_limit_approval.credit_approval')


    def call_wizard(self):
        wizard_form = self.env.ref('credit_limit_alert.credit_limit_alert_partner_statement_wizard_view', False)
        view_id = self.env['credit_limit_alert.partner_statement_wizard']
        vals = {
            'name': 'this is for set name',
            'str_partner_id': self.id,
        }
        new = view_id.create(vals)
        return {
            'name': _('Reporte de estado de deudas de ' + self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'credit_limit_alert.partner_statement_wizard',
            'res_id': new.id,
            'view_id': wizard_form.id,
            'view_mode': 'form',
            'target': 'new'
        }


