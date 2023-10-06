from odoo import api, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        # Appeler la méthode create originale
        res = super(AccountMove, self).create(vals)

        # Si c'est une facture (vous pouvez ajouter d'autres conditions si nécessaire)
        if res.move_type in ['in_invoice', 'out_invoice']:
            # Déclenchez le calcul des lignes de TVA
            self.env['planned.money'].create_or_update_vat_lines()
            self.env['planned.money'].handle_treasury_line(res.id)

        return res

    def action_post(self):
        # Appeler la méthode action_post originale
        res = super(AccountMove, self).action_post()

        # Si c'est une facture (vous pouvez ajouter d'autres conditions si nécessaire)
        if self.move_type in ['in_invoice', 'out_invoice']:
            # Déclenchez le calcul des lignes de TVA
            self.env['planned.money'].create_or_update_vat_lines()
            self.env['planned.money'].handle_treasury_line(self.id)

        return res


