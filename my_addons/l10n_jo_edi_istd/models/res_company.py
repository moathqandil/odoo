# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_jo_activity_number = fields.Char(string='Activity Number', help='Activity Number In ISTD Portal')

    l10n_jo_client_id = fields.Char(string='Client ID', groups="base.group_erp_manager")
    l10n_jo_client_secret = fields.Char(string='Client Secret', groups="base.group_erp_manager")
    l10n_jo_send_invoices_at_confirm = fields.Boolean(string='Send Invoices At Confirm', groups="base.group_erp_manager")
