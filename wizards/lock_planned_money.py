from odoo import models, fields

class LockPlannedMoney(models.TransientModel):
    _name = 'lock.planned.money'
    _description = 'Verrouillage de ligne de trésorerie'

    lines = fields.Many2many('planned.money', string='Lignes')

    def confirm_date(self):
        for line in self.lines:
            line.lock_button()