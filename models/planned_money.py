from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import timedelta ,datetime, date
from odoo.exceptions import ValidationError

class MoneyAmount(models.Model):

    _name="planned.money"
    _description="Prévision de trésorerie"
    _order = "date asc "

    @api.model
    def _initial_lignes(self):
        obj = self.env['planned.money'].search([]).mapped('id')
        if obj != False :
            return len(obj)
        else:
            return False

    @api.model
    def _default_date(self):
        obj = self.env['planned.money'].search([])
        if obj != False :
            if len(obj)<2: 
                current = datetime.now().replace(month=1, day=1, hour=00, minute=00, second=5)
            else :
                current = datetime.now()
            return current

    name = fields.Char(string="Ref",readonly=True, required=True, copy=False, default='Nouveau')
    add_line = fields.Selection([('stat_line','Situation'),('standard_line','Standard')], string='Type', required=True, default='standard_line')
    line = fields.Char(string="Ligne",compute='_compute_line',)
    partner_id = fields.Many2one("res.partner", string="Partenaire")
    company_id = fields.Many2one("res.company", string="Société",default=lambda self: self.env.company)
    type_id = fields.Many2one("types.planned.money", string="Compte" ,required=True)
    date = fields.Datetime(string="Date" , select=True)
    predicted_date = fields.Datetime(string="Date prévue" ,default=_default_date, select=True)
    due_date=fields.Datetime(string="Date effective")
    input_amount=fields.Monetary(string="Montant d'entrée")
    output_amount=fields.Monetary(string="Montant de sortie")
    balance = fields.Monetary(string="Balance", tracking=True , compute='compute_balance')
    previous_balance=fields.Monetary(string="Solde n-1",compute='_compute_cumulated_balance' )
    provisional_balance=fields.Monetary(string="Solde", compute='_compute_cumulated_balance')
    situation = fields.Monetary(string="Situation initiale")
    sequences = fields.Integer(string="Séquence", default=100)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id)
    check = fields.Boolean(default=False)
    start_date = fields.Datetime(string="Date de début", default=fields.Datetime.now,)
    label = fields.Char(string="Désignation") 
    state = fields.Selection([('predicted','Prévu'),('in_progres','En cours'),('done','Fait')], string="État", default='predicted')
    end_date = fields.Datetime(string="Date de fin")
    week = fields.Selection([('6','Dimanche'),('0','Lundi'),('1','Mardi'),('2','Mercredi'),('3','Jeudi'),('4','Vendredi'),('5','Samedi')])
    month = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),('6','6'),('7','7'),('8','8'),('9','9'),('10','10'),('11','11'),('12','12'),('13','13'),('14','14'),('15','15'),('16','16'),('17','17'),('18','18'),('19','19'),('20','20'),('21','21'),('22','22'),('23','23'),('24','24'),('25','25'),('26','26'),('27','27'),('28','28'),('29','29'),('30','30'),('31','31')])  
    date_type = fields.Selection([('day','Day'),('week','Semaine'),('month','Mois')],string="Récurrence")
    groupe = fields.Char(string="Groupe",readonly=False, required=True, copy=False, default ="000")
    lock_status = fields.Selection([('locked','✅'),('in_progres','⬅️'),('unlocked','')], default='unlocked',compute='_compute_status')
    category_id = fields.Many2one('line.categories' , string = "Catégorie")
    invoice_id = fields.Many2one('account.move', string='N° de Facture', help='Lien vers la facture associée')

    
    @api.depends('state')
    def _compute_status(self):
        for rec in self :
            if rec.state == "predicted":
                rec.lock_status = "unlocked"
            elif rec.state == "in_progres":
                rec.lock_status = "in_progres"
            else:
                rec.lock_status = "locked"

    @api.model
    def writeon(self, vals):
        return models.Model.write(self, vals)

    @api.model
    def creaton(self, vals):
        return models.Model.create(self, vals)

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nouveau') == 'Nouveau':
            vals['name'] = self.env['ir.sequence'].next_by_code('planned.money') or 'Nouveau'

        if vals["state"] != "done" :
            vals["date"] = vals["predicted_date"]

        if vals["add_line"] == "stat_line":

            if vals.get('groupe', '000') == '000':
                vals['groupe'] = self.env['ir.sequence'].next_by_code('planned_money') or '000'

            obji = self.env['types.planned.money'].search([('id',"!=",vals["type_id"])]).mapped('id')
            if obji!= False and (len(obji)+1) <= self._initial_lignes():
                for i in range(len(obji)):
                    self.env['planned.money'].creaton({
                        "add_line":"stat_line",
                        "label":vals['label'],
                        "name":vals['name'],
                        "type_id":obji[i],
                        "predicted_date": vals['predicted_date'],
                        "situation": vals['situation'],
                        "date": vals['date'],
                        })

        else:
            obj = self.env['planned.money'].search([('add_line',"=",'stat_line'),('date',"<",vals["date"]),('type_id',"=",vals["type_id"])],order = 'date desc').mapped('groupe')
            if obj:
                vals["groupe"]= obj[0]
            else:
                vals["groupe"] = self.env['ir.sequence'].next_by_code('planned_money') or '000'
        
        result = super(MoneyAmount, self).create(vals)
        if vals["add_line"] == "stat_line":
            for rec in result:
                obji = self.env['planned.money'].search([('add_line',"!=",'stat_line'),('date',">=",rec.date),('type_id',"=",rec.type_id.id)])
                if obji != False:
                        obji.writeon({
                            "groupe":vals["groupe"],
                            })
        return result 

    def write(self, vals):
        for rec in self:
            if rec.add_line != "stat_line":
                obj = rec.env['planned.money'].search([('add_line',"=",'stat_line'),('date',"<",self.date),('type_id',"=",self.type_id.id)],order = 'date desc').mapped('groupe')
                if obj:
                    vals["groupe"]= obj[0]
        
        return super(MoneyAmount, self).write(vals)

    def lock_button(self):
        for rec in self:
            if rec.state == "done":
                raise UserError("Vous ne pouvez pas verrouiller une ligne qui est déjà verrouillée")

            rec.date = rec.due_date
            rec.state = "done"

            planned_obj = rec.env['planned.money'].search([('date','>',rec.date),('type_id','=',rec.type_id.id)],order = 'date asc' ,limit=1)

            if not planned_obj:
                return
            if planned_obj.state == "predicted":
                planned_obj.state = "in_progres"
                    
    def unlock_button(self):
        for rec in self:
            if rec.state != "done":
                raise UserError("Vous ne pouvez pas déverrouiller une ligne qui n'est pas verrouillée")
            if rec.state == "done":
                rec.state = "in_progres"


    def up_button(self):
        for rec in self:
            if rec.state == "done":
                raise UserError("Vous ne pouvez pas déplacer une ligne vérrouillée")
            else:
                planned_obj = rec.env['planned.money'].search([('date','<',rec.date)],order = 'date desc' ,limit=2).mapped('date')
                if planned_obj:
                    rec.date = planned_obj[1] + timedelta(minutes=5)
                    rec.predicted_date =  planned_obj[1] + timedelta(minutes=5)

    def down_button(self):
        for rec in self:
            if rec.state == "done":
                raise UserError("Vous ne pouvez pas déplacer une ligne vérrouillée")
            else:
                planned_obj = rec.env['planned.money'].search([('date','>=',rec.date),('id','!=',rec.id)],order = 'date asc' ,limit=1).mapped('date')
                if planned_obj:
                    rec.date = planned_obj[0] + timedelta(minutes=5)
                    rec.predicted_date =  planned_obj[0] + timedelta(minutes=5)

    def button_external(self):
        view = {
            'name':"details",
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'planned.money',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'readonly': True,
            'res_id': self.id,
        }
        return view

    def update_icon(self, model_name, active_id):
        current_id = self.id
        for line in self.env['planned.money'].search([]):
            line.check =False
            if line.id == current_id:
                line.check = True     
    
      

    def archived_planned_money(self):
        moneys = self.env['planned.money']
        active_ids = self.env.context.get('active_ids', [])
        actvs = self.with_context(moneys=active_ids)
        if len(actvs) > 1 :
            raise ValidationError("Vous ne pouvez pas archiver plus d'un enregistrement")
        elif actvs.add_line != ('stat_line'):
            raise ValidationError("On ne peux sélectionné qu'une ligne de situation")
        compt = actvs.type_id.name
        typ = actvs.add_line
        liste = [actvs]
        if actvs.id == 1 or actvs.id == 2:
            mony_ids = self.env['planned.money'].search([('date','>=',actvs.date)])
        else:
            mony_ids = self.env['planned.money'].search([('due_date','>=',actvs.due_date)])

        for record in mony_ids:
            if record != mony_ids[0]: 
                if record.add_line == typ:
                    break
                if record.type_id.name == compt and  record.add_line != typ:
                    liste.append(record)   
    
        for st in liste:
            if st.state !=('done'):
                raise ValidationError("L'une des lignes récupérer n'est pas à l'état faite")
            else:
                self.env['planned.money.archive'].sudo().create(
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
                    }
                ) 
                st.unlinkon()

    """
    function to test if date is expired than archive this record
    first give all seq = 10 then each time we archive a record we add to it's seq 1,
    this will help us to order the archived_tree by using this field seq
    """
    
    @api.depends('input_amount','output_amount','situation','previous_balance',)
    def compute_balance(self):
        for rec in self :
            if rec.add_line == "stat_line":
                rec.balance = (rec.situation - rec.previous_balance)
            else:
                rec.balance = (rec.input_amount - rec.output_amount)

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
            # domain_cumulated_test=[('groupe','=',record.groupe)]
            query = self._where_calc(list([] or []))
            order_string = ", ".join(self._generate_order_by_inner(self._table, self.env.context.get('order_cumulated_balance'), query ,reverse_direction=False))
            from_clause, where_clause, where_clause_params = query.get_sql()
            sql = """
                SELECT planned_money.id, 
                CASE when planned_money.add_line ='stat_line' AND '%(previous_line)s' = 'predicted' then planned_money.situation
                when planned_money.add_line ='stat_line' AND '%(previous_line)s' = 'stat_line' then planned_money.situation + '%(n)s'
                when (planned_money.add_line ='standard_line')then planned_money.input_amount - planned_money.output_amount + '%(n)s'
                ELSE 
                SUM(CASE 
                when (planned_money.add_line ='stat_line') AND ('%(previous_line)s' = 'stat_line') then(planned_money.situation)
                /*when (planned_money.add_line ='standard_line') then planned_money.input_amount - planned_money.output_amount */
                ELSE planned_money.situation
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

    """
    this function will be called when click in button
    """
    @api.model
    def update_treeview(self, model_name, active_id):
        res = self.env['planned.money'].search([('company_id','=',self.env.company.id)])
        for r in res:
            r.compute_amounts()
    """
    function to delete lines / rows in tree view
    """
    def unlink(self):
        for line in self:
            if line.state == "done":
                raise UserError('Vous ne pouvez pas supprimer un enregistrement à l\'état "Fait"')
        return super(MoneyAmount, self).unlink()

    @api.model
    def unlinkon(self):
        return models.Model.unlink(self)

    #some modifications
    @api.onchange('predicted_date','state')
    def onchange_due_date(self):
        if self.state in ['in_progres','predicted']:
            self.date = self.predicted_date
    
    #Montant automatique facture
    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        # Réinitialisez les montants et les dates
        self.input_amount = 0.0
        self.output_amount = 0.0
        self.predicted_date = False
        self.due_date = False
        self.category_id = 2

        if self.invoice_id:
            # Si c'est une facture fournisseur
            if self.invoice_id.move_type == 'in_invoice':
                self.output_amount = self.invoice_id.amount_total  # Montant de sortie pour les dépenses
                self.label = 'Facture fournisseur'
                
            # Si c'est une facture client
            elif self.invoice_id.move_type == 'out_invoice':
                self.input_amount = self.invoice_id.amount_total  # Montant d'entrée pour les entrées
                self.label = 'Facture client'

            # Mettez à jour les champs de date avec la date d'échéance de la facture
            self.predicted_date = self.invoice_id.invoice_date_due
            self.due_date = self.invoice_id.invoice_date_due
            self.type_id = 1
            self.partner_id = self.invoice_id.partner_id
            self.update_treeview('planned.money', self.id)


    @api.model
    def create_or_update_vat_lines(self):
        today = date.today()
        first_day_of_current_month = date(today.year, today.month, 1)
        last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
        first_day_of_previous_month = date(last_day_of_previous_month.year, last_day_of_previous_month.month, 1)

        # Calculer la somme de la TVA pour le mois précédent
        previous_month_vat = sum(self.env['account.move'].search([
            ('invoice_date_due', '>=', first_day_of_previous_month),
            ('invoice_date_due', '<=', last_day_of_previous_month),
        ]).mapped('amount_tax_signed'))

        # Calculer la somme de la TVA pour le mois en cours
        current_month_vat = sum(self.env['account.move'].search([
            ('invoice_date_due', '>=', first_day_of_current_month),
            ('invoice_date_due', '<', today),  # Jusqu'à la date d'aujourd'hui
        ]).mapped('amount_tax_signed'))

        # Traitement pour le mois précédent
        vals_previous_month = {
            'predicted_date': date(today.year, today.month, 15),
            'state': 'predicted',
            'label': 'TVA',
            'add_line': 'standard_line',
            'type_id': 1,
            'category_id': 3
        }
        if previous_month_vat < 0:
            vals_previous_month['output_amount'] = abs(previous_month_vat)
        else:
            vals_previous_month['input_amount'] = previous_month_vat

        existing_line_current_month = self.search([('predicted_date', '=', date(today.year, today.month, 15)), ('label', '=', 'TVA')], limit=1)
        if existing_line_current_month:
            existing_line_current_month.write(vals_previous_month)
        else:
            self.create(vals_previous_month)

        # Traitement pour le mois en cours
        next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)  # Trouver le premier jour du mois suivant
        vals_current_month = {
            'predicted_date': date(next_month.year, next_month.month, 15),
            'state': 'predicted',
            'label': 'TVA',
            'add_line': 'standard_line',
            'type_id': 1,
            'category_id': 3
        }
        if current_month_vat < 0:
            vals_current_month['output_amount'] = abs(current_month_vat)
        else:
            vals_current_month['input_amount'] = current_month_vat

        existing_line_next_month = self.search([('predicted_date', '=', date(next_month.year, next_month.month, 15)), ('label', '=', 'TVA')], limit=1)
        if existing_line_next_month:
            existing_line_next_month.write(vals_current_month)
        else:
            self.create(vals_current_month)
        
        self.update_treeview('planned.money', self.id)

    @api.model   
    def create_salary_and_urssaf_lines(self):
        today = date.today()
        month = today.month

        # Vérifiez si nous sommes en juin ou en décembre
        increase_percentage = 1.5 if month in [6, 12] else 1

        # Définissez les montants pour le salaire et l'Urssaf
        base_salary_amount = 3646  # Montant de base pour le salaire
        base_urssaf_amount = 2691  # Montant de base pour l'Urssaf

        # Appliquez l'augmentation si nécessaire
        salary_amount = base_salary_amount * increase_percentage
        urssaf_amount = base_urssaf_amount * increase_percentage

       # Vérifiez si un enregistrement "Salaires" existe pour le 1er du mois en cours
        existing_salary_record = self.search([
            ('predicted_date', '=', date(today.year, today.month, 1)),
            ('label', '=', 'Salaires')
        ])
        if not existing_salary_record:
            # Créer une ligne de trésorerie pour le salaire
            self.create({
                'output_amount': salary_amount,
                'predicted_date': date(today.year, today.month, 1),  # 1er du mois en cours
                'state': 'predicted',
                'label': 'Salaires',
                'add_line': 'standard_line',
                'type_id': 1,
                'category_id': 3
            })

        # Vérifiez si un enregistrement "URSSAF" existe pour le 15 du mois en cours
        existing_urssaf_record = self.search([
            ('predicted_date', '=', date(today.year, today.month, 15)),
            ('label', '=', 'URSSAF')
        ])
        if not existing_urssaf_record:
            # Créer une ligne de trésorerie pour l'Urssaf
            self.create({
                'output_amount': urssaf_amount,
                'predicted_date': date(today.year, today.month, 15),  # 15 du mois en cours
                'state': 'predicted',
                'label': 'URSSAF',
                'add_line': 'standard_line',
                'type_id': 1,
                'category_id': 3
            })
        self.update_treeview('planned.money', self.id)

    @api.model
    def handle_treasury_line(self, invoice_id):
        # Récupérer l'enregistrement de la facture
        record = self.env['account.move'].browse(invoice_id)

        if record.payment_state == 'not_paid':
            # Vérifiez si une ligne de trésorerie existe déjà pour cette facture
            treasury_line = self.search([('invoice_id', '=', record.id)])
            
            # Déterminez si c'est une facture client ou fournisseur
            if record.move_type == 'out_invoice':  # Facture client
                field_to_update = 'input_amount'
                label = 'Facture Client'
            elif record.move_type == 'in_invoice':  # Facture fournisseur
                field_to_update = 'output_amount'
                label = 'Facture Fournisseur'
            else:
                return  # Si ce n'est ni une facture client ni une facture fournisseur, sortez de la fonction

            if not treasury_line:
                # Créez une nouvelle ligne de trésorerie si elle n'existe pas
                self.create({
                    'invoice_id': record.id,
                    field_to_update: record.amount_total,
                    'predicted_date': record.invoice_date_due,
                    'state': 'predicted',
                    'label': label,
                    'add_line': 'standard_line',
                    'type_id': 1,
                    'category_id': 3
                })
            else:
                # Mettez à jour la ligne de trésorerie existante si nécessaire
                treasury_line.write({
                    field_to_update: record.amount_total,
                    'predicted_date': record.invoice_date_due,
                    'state': 'predicted',
                    'label': label,
                    'add_line': 'standard_line',
                    'type_id': 1,
                    'category_id': 3
                })
        self.update_treeview('planned.money', self.id)

