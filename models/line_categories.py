from odoo import api, fields, models


class LineCategories(models.Model):

    _name = "line.categories"
    _description = "Catégorie de ligne de trésorerie"
    
    name = fields.Char(string="Nom")