from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError,Warning
from datetime import date, timedelta ,datetime

class PlannedPeriodique(models.TransientModel):
    _name = 'planned.periodique'
    _description = 'Creation of cyclic lines'


    @api.model
    def _default_date(self):
        obj = self.env['planned.money'].search([])
        if obj != False :
            if len(obj)<2: 
                current = datetime.now().replace(month=1, day=1, hour=00, minute=00, second=5)
            else :
                current = datetime.now()
            return current


    partner_id = fields.Many2one("res.partner", string="Partenaire")
    
    company_id = fields.Many2one("res.company", string="Company",default=lambda self: self.env.company)

    type_id = fields.Many2one("types.planned.money", string="Compte" ,required=True)

    input_amount=fields.Monetary(string="Montant d'entrée")

    output_amount=fields.Monetary(string="Amount output")
    
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id)

    start_date = fields.Datetime(string="Date de début", default=fields.Datetime.now, required=True)

    label = fields.Char(string="Label")

    end_date = fields.Datetime(string="Date de fin" ,required=True)

    week = fields.Selection([('6','Dimanche'),('0','Lundi'),('1','Mardi'),('2','Mercredi'),('3','Jeudi'),('4','Vendredi'),('5','Samedi')])
    
    month = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),('6','6'),('7','7'),('8','8'),('9','9'),('10','10'),('11','11'),('12','12'),('13','13'),('14','14'),('15','15'),('16','16'),('17','17'),('18','18'),('19','19'),('20','20'),('21','21'),('22','22'),('23','23'),('24','24'),('25','25'),('26','26'),('27','27'),('28','28'),('29','29'),('30','30'),('31','31')])  
    
    date_type = fields.Selection([('day','Day'),('week','Semaine'),('month','Month')],string='Réccurence')

    add_line = fields.Selection([('stat_line','Situation'),('standard_line','Standard')], string='Type', required=True, default='standard_line')

    situation = fields.Monetary(string="Situation initiale")

    predicted_date = fields.Datetime(string="Date prévue" ,default=_default_date, required=False, readonly=False, select=True)

    date = fields.Datetime(string="Date" ,default=_default_date, required=False, readonly=False, select=True)

    
    def date_range(self,start, end):
        fmt = '%Y-%m-%d %H:%M:%S'
        s = str(start)
        e = str(end)
        d1 = datetime.strptime(s, fmt)
        d2 = datetime.strptime(e, fmt)

        delta = d2 - d1  # as timedelta
        days = [d1 + timedelta(days=i) for i in range(delta.days + 1)]
        return days

    def create_periodique(self):
        planned_obj = self.env['planned.money'].search([])
        interval = self.date_range(self.start_date, self.end_date)
        if not interval:
            raise UserError("La date de début doit être inférieur à la date du fin ")

        count = 0            
        if self.date_type == "month":
            data = []
            selected_day = int(self.month)
            interval_days = [int(i.day) for i in interval]
            if int(self.month) not in interval_days:
                raise UserError("Cette date n'existe pas dans l'interval des dates ") 
            for i in range(len(interval)):
                if selected_day == interval[i].day:
                    count += 1
                    data.append(interval[i])

            if self.add_line == "stat_line":
                for j in range(count):
                    planned_obj.create({
                        "add_line":"stat_line",
                        "label":self.label,
                        "type_id":self.type_id.id,
                        "start_date":self.start_date,
                        "end_date":self.end_date,
                        "situation": self.situation,
                        "predicted_date": data[j],
                        "state": "predicted",
                        "date": data[j],
                        })
            else:
                for j in range(count):
                    planned_obj.create({
                        "add_line":self.add_line,
                        "label":self.label,
                        "type_id":self.type_id.id,
                        "input_amount":self.input_amount,
                        "output_amount":self.output_amount,
                        "start_date":self.start_date,
                        "end_date":self.end_date,
                        "partner_id":self.partner_id.id,
                        "predicted_date": data[j],
                        "state": "predicted",
                        "date": data[j],
                        })

            self.predicted_date = data[0]            
        if self.date_type == "week":
            data = []
            selected_week = int(self.week)
            interval = self.date_range(self.start_date, self.end_date)


            for i in range(len(interval)):
                if selected_week == interval[i].weekday():
                    count += 1
                    data.append(interval[i])

            if self.add_line == "stat_line":
                for j in range(count):
                    planned_obj.create({
                        "add_line":"stat_line",
                        "label":self.label,
                        "type_id":self.type_id.id,
                        "start_date":self.start_date,
                        "end_date":self.end_date,
                        "situation": self.situation,
                        "predicted_date": data[j],
                        "state": "predicted",
                        "date": data[j],
                        })
            else:
                for j in range(count):
                    planned_obj.create({
                        "add_line":self.add_line,
                        "label":self.label,
                        "type_id":self.type_id.id,
                        "input_amount":self.input_amount,
                        "output_amount":self.output_amount,
                        "start_date":self.start_date,
                        "end_date":self.end_date,
                        "partner_id":self.partner_id.id,
                        "predicted_date":data[j],
                        "state": "predicted",
                        "date": data[j],
                        })                    
            self.predicted_date = data[0]

        if self.date_type == "day":
            interval = self.date_range(self.start_date, self.end_date)
            if self.add_line == "stat_line":
                for i in range(len(interval)):
                    planned_obj.create({
                        "add_line":"stat_line",
                        "label":self.label,
                        "type_id":self.type_id.id,
                        "start_date":self.start_date,
                        "end_date":self.end_date,
                        "situation": self.situation,
                        "predicted_date": interval[i],
                        "state": "predicted",
                        })
            else:
                for i in range(len(interval)):
                    planned_obj.create({
                        "add_line":"standard_line",
                        "label":self.label,
                        "type_id":self.type_id.id,
                        "input_amount":self.input_amount,
                        "output_amount":self.output_amount,
                        "start_date":self.start_date,
                        "end_date":self.end_date,
                        "partner_id":self.partner_id.id,
                        "state": "predicted",
                        "predicted_date": interval[i],
                        })

        action = {
          'name' :'recurrentes close action',
          'type': 'ir.actions.act_window_close',
          'res_model': 'planned.periodique',
                }
        

        tree_view_id = self.env.ref('eloapps_cash_flow_forecast.view_tree_model_cash_flow_forecast').ids
        form_view_id = self.env.ref('eloapps_cash_flow_forecast.view_form_model_cash_flow_forecast').ids

        return {

                'type': 'ir.actions.act_window',
                'name': 'recurrentes close action',
                'res_model': 'planned.money',
                'view_mode': 'tree',
                'views': [[tree_view_id, 'tree'], [form_view_id, 'form']],
                'target': 'current',

            }
        
        