from odoo import models,Command

class EstateProperty(models.Model):
    _inherit = "estate.property"

    def property_sold(self):
        journal = self.env["account.journal"].search([("type", "=", "sale")], limit=1)

        for order in self:
            order.env["account.move"].create(
                {
                    "partner_id": order.buyer_id.id,
                    "move_type": "out_invoice",
                    "journal_id": journal.id,
                    "invoice_line_ids": [
                        Command.create({
                            "name": "estate price",
                            "quantity": 1,
                            "price_unit":  order.selling_price * 0.06
                        }),
                        Command.create({
                            "name": "administrative fees",
                            "quantity": 1,
                            "price_unit":  100
                        })
                    ]
                }
            )
        return super().property_sold()
