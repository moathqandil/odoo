from odoo import models,fields,api
from odoo.exceptions import UserError,ValidationError
from datetime import date,timedelta,datetime
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "The Model contains the property for each real estate"
    _order = "sequence, id desc"

    name = fields.Char(required=True, string="Title")
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
    statuses = [('R','Offer Recieved'),('A','Offer Accepted'),('N','New'),('C','Canceled'),('S','Sold')]
    state = fields.Selection(statuses, default='N')
    active = fields.Boolean(default=True)
    property_type_id = fields.Many2one("estate.property.type", string="type")
    buyer_id = fields.Many2one("res.partner", string="buyer",copy=False)
    salesperson_id = fields.Many2one("res.partner", string="salesperson",default=lambda self: self.env.user)
    tag_ids = fields.Many2many("estate.property.tag", string="Tags")
    offer_ids = fields.One2many("estate.property.offer", "property_id", string="offers")
    total_area = fields.Integer(compute="_compute_total_area", string="Total Area (sqm)", store=True)
    best_price = fields.Float(compute="_compute_best_prices", store=True)
    sequence = fields.Integer('Sequence', default=1, help="Used to order properties. Lower is better.")
    user_id = fields.Many2one("res.users", string = "users")

    _sql_constraints =[
    ('check_expected_price','CHECK(expected_price >= 0)',
    'The expected price must be positive'),
    ('check_selling_price','CHECK(selling_price >= 0)',
    'The selling price must be positive')
    ]

    @api.constrains("selling_price")
    def _check_selling_price90(self):   # QUESTION:
        for property in self:
            if not float_is_zero(property.selling_price,2) and float_compare(property.selling_price,property.expected_price * 0.9,2) < 1:
                raise ValidationError(f"The selling price has to be atleast 90% of the expected price ({property.expected_price * 0.9})")


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

    def property_sold(self):
        for property in self:
            if property.state == 'C':
                # if the property has been canceled, then it can't be sold
                raise UserError("Canceled properties cannot be sold")
            else:
                property.state = 'S'
        return True


    def property_cancel(self):
        for property in self:
            if property.state == 'S':
                # if the property has been canceled, then it can't be sold
                raise UserError("Sold properties cannot be canceled")
            else:
                property.state = 'C'

        return True

    @api.ondelete(at_uninstall=False)
    def _unlink_if_state_NC(self):
        for property in self:
            if property.state not in ['C','N']:
                raise UserError("Only canceld and new properties can be deleted")






class PropertyType(models.Model):
    _name = "estate.property.type"
    _description = "The Model contains the types of the properties"
    _order = "name"

    name = fields.Char(required=True)
    property_ids = fields.One2many("estate.property","property_type_id",string="properties")
    offer_ids = fields.One2many("estate.property.offer","property_type_id",string="Offers")
    offer_count = fields.Integer(compute="_count_offers")

    _sql_constraints =[
    ('check_type_uniquity','UNIQUE(name)',
    'The property type must be positive')
    ]

    @api.depends("offer_ids")
    def _count_offers(self):
        self.offer_count = len(self.offer_ids)


class PropertyTag(models.Model):
    _name = "estate.property.tag"
    _description = "The Model contains tags to add to the Estate properties"
    _order = "name"

    name = fields.Char(required=True)
    color = fields.Integer()

    _sql_constraints =[
    ('check_tag_uniquity','UNIQUE(name)',
    'The property tag must be unique')
    ]

class PropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "The Model contains offers on existing properties"
    _order = "price desc"

    price = fields.Float()
    choises_status = [('A','Accepted'),('R','Refused')]
    state = fields.Selection(choises_status, copy=False)
    partner_id = fields.Many2one("res.partner",required=True)
    property_id = fields.Many2one("estate.property",required=True)
    validity = fields.Integer(default=7, string="Validity (days)")
    date_deadline = fields.Date(compute="_compute_deadline", inverse="_inverse_deadline",store=True)
    property_type_id = fields.Many2one(related="property_id.property_type_id",store=True)

    _sql_constraints =[
    ('check_offer_price','CHECK(price > 0)',
    'The offer price must be positive')
    ]

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

    def offer_accept(self):
        for offer in self:
            for offer2 in offer.property_id.offer_ids:
                offer2.state = 'R' # Refuse all the offers, so we can accept the last one.

            property = self.property_id
            property.buyer_id = self.partner_id.id
            property.selling_price = self.price
            property.state = 'R'
            offer.property_id = property
            offer.state = 'A'
        return True

    def offer_refuse(self):
        for offer in self:
            offer.state = 'R'
        return True

    @api.model
    def create(self, vals):
        self.env['estate.property'].browse(vals['property_id']).state = 'R'
        best_price = self.env['estate.property'].browse(vals['property_id']).best_price
        if vals['price'] < best_price:
            raise UserError("Your offer should be higher than the highest offer")
        else:
            return super().create(vals)
