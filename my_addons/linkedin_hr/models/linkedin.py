from odoo import models,Command,fields

class Linkedin(models.Model):
    _inherit = "hr.applicant"

    linkedin = fields.Char('URL', default="google.com")
