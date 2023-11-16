from odoo import models,fields,api

class EstateUsers(models.Model):

    _inherit = "res.users"

    property_ids = fields.One2many("estate.property","user_id",string="properties",domain=[("state", "in", ['N', 'R'])])
