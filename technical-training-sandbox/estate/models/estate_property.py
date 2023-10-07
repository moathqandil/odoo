from odoo import models,fields
from datetime import date,timedelta

class EstateProperty(models.Model):
    _name = "estate.property"

    _description = "The Model contains the property for each real estate"

    name = fields.Char(required=True)
    description = fields.Text(default='')
    Postcode = fields.Char(default='')
    date_availability = fields.Date(copy=False,default=date.today() + timedelta(days=90))
    expected_price = fields.Float(required=True,default=0)
    selling_price = fields.Float(readonly=True,copy=False,default=0)
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer(default=0)
    facades = fields.Integer(default=0)
    garage = fields.Boolean(default=False)
    garden = fields.Boolean(default=False)
    garden_area = fields.Integer(default=0)
    orientaitons = [('X',''),('N','North'),('E','East'),('W','West'),('S','South')]
    garden_orientation = fields.Selection(orientaitons,default='X')
    statuses = [('OR','Offer Recieved'),('NE','New')]
    status = fields.Selection(statuses, default='NE')
    active = fields.Boolean(default=True)

class PropertyType(models.Model):
    _name = "estate.property.type"
    _description = "The Model contains the types of the properties"

    name = fields.Char(required=True)
