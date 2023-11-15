from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_jo_client_id = fields.Char(related='company_id.l10n_jo_client_id', readonly=False)
    l10n_jo_client_secret = fields.Char(related='company_id.l10n_jo_client_secret', readonly=False)
    l10n_jo_send_invoices_at_confirm = fields.Boolean(related='company_id.l10n_jo_send_invoices_at_confirm', readonly=False)
