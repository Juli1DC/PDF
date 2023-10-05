from odoo import api, fields, models
from odoo.exceptions import ValidationError

class MoneyAmount(models.Model):

    _name="planned.money.archive"
    _description="Prévision de trésorerie archivée"
    _order = "date asc "

    name = fields.Char(string="Ref",readonly=True, required=True, copy=False, default='Nouveau')
    add_line = fields.Selection([('stat_line','Situation'),('standard_line','Standard')], string='Type', required=True, default='standard_line')
    partner_id = fields.Many2one("res.partner", string="Partenaire")
    company_id = fields.Many2one("res.company", string="Société",default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id)
    type_id = fields.Many2one("types.planned.money", string="Compte" ,required=True)
    date = fields.Datetime(string="Date" , select=True)
    due_date=fields.Datetime(string="Date effective")
    situation = fields.Monetary(string="Situation initiale")
    input_amount=fields.Monetary(string="Montant d'entrée")
    output_amount=fields.Monetary(string="Montant de sortie")
    previous_balance=fields.Monetary(string="Solde n-1", compute='_compute_cumulated_balance' )
    provisional_balance=fields.Monetary(string="Solde", compute='_compute_cumulated_balance')
    label = fields.Char(string="Désignation") 
    category_id = fields.Many2one('line.categories' , string = "Catégorie")

    def desarchived_planned_money(self):
        moneys = self.env['planned.money.archive']
        active_ids = self.env.context.get('active_ids', [])
        actvs = self.with_context(moneys=active_ids)

        if len(actvs) > 1 :
            raise ValidationError("vous ne pouvez pas archiver plus d'un enregistrement")
        elif actvs.add_line != ('stat_line'):
            raise ValidationError("On ne peux sélectionné qu'une ligne de situation")

        compt = actvs.type_id.name
        typ = actvs.add_line
        liste = [actvs]
        mony_ids = self.env['planned.money.archive'].search([('date','>=',actvs.date)])
        for record in mony_ids:
            if record != mony_ids[0]: 
                if record.add_line == typ:
                    break
                if record.type_id.name == compt and  record.add_line != typ:
                    liste.append(record)   
    
        for st in liste:
            self.env['planned.money'].sudo().creaton(
                {
                    'label':st.label,
                    'add_line':st.add_line,
                    'partner_id':st.partner_id.id,
                    'type_id':st.type_id.id,
                    'category_id':st.category_id.id,
                    'date':st.date,
                    'due_date':st.due_date,
                    'input_amount':st.input_amount,
                    'output_amount':st.output_amount,
                    'situation':st.situation,
                    'state':'done',
                }
            )  
            st.unlink()

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        def to_tuple(t):
            return tuple(map(to_tuple, t)) if isinstance(t, (list, tuple)) else t
        # Make an explicit order because we will need to reverse it
        order = (order or self._order) + ', id'
        # Add the domain and order by in order to compute the cumulated balance in _compute_cumulated_balance
        return super(MoneyAmount, self.with_context(domain_cumulated_balance=to_tuple(domain or []), order_cumulated_balance=order)).search_read(domain, fields, offset, limit, order)

    @api.depends_context('order_cumulated_balance', 'domain_cumulated_balance')
    def _compute_cumulated_balance(self):

        a = self.env.context.get('domain_cumulated_balance')
        if not self.env.context.get('order_cumulated_balance'):
            # We do not come from search_read, so we are not in a list view, so it doesn't make any sense to compute the cumulated balance
            self.provisional_balance = 0
            self.previous_balance = 0
            return

        n = 0
        previous_line = "predicted"
        for record in self:
            query = self._where_calc(list([] or []))
            order_string = ", ".join(self._generate_order_by_inner(self._table, self.env.context.get('order_cumulated_balance'), query ,reverse_direction=False))
            from_clause, where_clause, where_clause_params = query.get_sql()
            sql = """
                SELECT planned_money_archive.id, 
                CASE when planned_money_archive.add_line ='stat_line' AND '%(previous_line)s' = 'predicted' then planned_money_archive.situation
                when planned_money_archive.add_line ='stat_line' AND '%(previous_line)s' = 'stat_line' then planned_money_archive.situation + '%(n)s'
                when (planned_money_archive.add_line ='standard_line')then planned_money_archive.input_amount - planned_money_archive.output_amount + '%(n)s'
                ELSE 
                SUM(CASE 
                when (planned_money_archive.add_line ='stat_line') AND ('%(previous_line)s' = 'stat_line') then(planned_money_archive.situation)
                /*when (planned_money_archive.add_line ='standard_line') then planned_money_archive.input_amount - planned_money_archive.output_amount */
                ELSE planned_money_archive.situation
                END) OVER(
                    ORDER BY %(order_by)s
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) END
                FROM %(from)s
                WHERE %(where)s
            """ % {'n':n,'previous_line':previous_line,'from': from_clause, 'where': where_clause or 'TRUE', 'order_by': order_string}
            self.env.cr.execute(sql, where_clause_params)
            result = {r[0]: r[1] for r in self.env.cr.fetchall()}

            key_list = []
            item_list = []
            for key ,item in result.items():
                key_list.append(item)
                item_list.append(key)

            record.previous_balance = n

            n = key_list[item_list.index(record.id)]
            if n == None:
                n = 0
            record.provisional_balance = result[record.id]
            if record.add_line == "stat_line":
                previous_line = "stat_line"
            else:
                previous_line = "predicted"
