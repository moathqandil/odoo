from odoo import models,fields
from datetime import date,timedelta

class TestModel(models.Model):
    _name = "test_model"

    _description = "Test Model"

    name = fields.Char(required=True)
    description = fields.Text(defualt='')
    Postcode = fields.Char(defualt='')
    date_availability = fields.Date(copy=False,default=date.today() + timedelta(days=90))
    expected_price = fields.Float(required=True,defualt=0)
    selling_price = fields.Float(readonly=True,copy=False,defualt=0)
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer(defualt=0)
    facades = fields.Integer(defualt=0)
    garage = fields.Boolean(defualt=False)
    garden = fields.Boolean(defualt=False)
    garden_area = fields.Integer(defualt=0)
    orientaitons = [('X','Choose'),('N','North'),('E','East'),('W','West'),('S','South')]
    garden_orientation = fields.Selection(orientaitons,default='X')
    statuses = [('OR','Offer Recieved'),('NE','New')]
    status = fields.Selection(statuses, default='NE')
    active = fields.Boolean(defualt=False)
