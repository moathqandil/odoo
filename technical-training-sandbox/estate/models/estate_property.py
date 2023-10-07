from odoo import models,fields,api
from datetime import date,timedelta,datetime

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
    living_area = fields.Integer(default=0, string="Living Area (sqm)")
    facades = fields.Integer(default=0)
    garage = fields.Boolean(default=False)
    garden = fields.Boolean(default=False)
    garden_area = fields.Integer(default=0, string="Garden Area (sqm)")
    orientaitons = [('X',''),('N','North'),('E','East'),('W','West'),('S','South')]
    garden_orientation = fields.Selection(orientaitons,default='X')
    statuses = [('OR','Offer Recieved'),('NE','New')]
    status = fields.Selection(statuses, default='NE')
    active = fields.Boolean(default=True)
    property_type_id = fields.Many2one("estate.property.type", string="type")
    buyer_id = fields.Many2one("res.users", string="buyer",copy=False)
    salesperson_id = fields.Many2one("res.partner", string="salesperson",default=lambda self: self.env.user)
    tag_ids = fields.Many2many("estate.property.tag", string="Tags")
    offer_ids = fields.One2many("estate.property.offer", "property_id", string="offers")
    total_area = fields.Integer(compute="_compute_total_area", string="Total Area (sqm)", store=True)
    best_price = fields.Float(compute="_compute_best_prices", store=True)

    @api.depends("living_area","garden_area")
    def _compute_total_area(self):
        for estate in self:
            estate.total_area = estate.living_area + estate.garden_area

    @api.depends("offer_ids.price")
    def _compute_best_prices(self):
        for record in self:
            try:
                record.best_price = max(offer.price for offer in record.offer_ids)
            except:
                record.best_price = 0

    @api.onchange("garden")
    def _onchange_partner_id(self):
        if self.garden:
            self.garden_area = 100
            self.garden_orientation = 'N'
        else:
            self.garden_area = 0
            self.garden_orientation = 'X'

class PropertyType(models.Model):
    _name = "estate.property.type"
    _description = "The Model contains the types of the properties"

    name = fields.Char(required=True)

class PropertyTag(models.Model):
    _name = "estate.property.tag"
    _description = "The Model contains tags to add to the Estate properties"

    name = fields.Char(required=True)

class PropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "The Model contains offers on existing properties"

    price = fields.Float()
    choises_status = [('A','Accepted'),('R','Refused')]
    status = fields.Selection(choises_status, copy=False)
    partner_id = fields.Many2one("res.partner",required=True)
    property_id = fields.Many2one("estate.property",required=True)
    validity = fields.Integer(default=7, string="Validity (days)")
    date_deadline = fields.Date(compute="_compute_deadline", inverse="_inverse_deadline",store=True)

    @api.depends("validity","create_date")
    def _compute_deadline(self):
        for offer in self:
            if offer.create_date:
                offer.date_deadline = offer.create_date + timedelta(days=offer.validity)
            else:
                offer.date_deadline = date.today() + timedelta(days=offer.validity)

    def _inverse_deadline(self):
        for offer in self:
            d1=datetime.strptime(str(datetime.date(self.create_date)),'%Y-%m-%d')
            d2=datetime.strptime(str(self.date_deadline),'%Y-%m-%d')
            d3=d2-d1
            offer.validity = str(d3.days)
