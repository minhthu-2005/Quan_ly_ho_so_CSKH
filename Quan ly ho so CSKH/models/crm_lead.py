from odoo import models, fields


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    interaction_history_ids = fields.One2many(
        'crm.interaction.history',
        'lead_id',
        string='Lịch sử tương tác'
    )