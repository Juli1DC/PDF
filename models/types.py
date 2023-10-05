from odoo import fields, models

class Types(models.Model):

    _name="types.planned.money"
    _description="Compte de trésorerie"

    name=fields.Char(string="Compte")