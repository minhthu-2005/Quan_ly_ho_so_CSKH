from odoo import models, fields


class CrmLead(models.Model):
    # KẾ THỪA MODULE CRM
    # Model crm.lead
    _inherit = 'crm.lead'

    # CUSTOM THÊM MỚI
    # Lưu danh sách Hồ sơ CSKH của Lead/Opportunity
    cskh_profile_ids = fields.One2many(
        'crm.cskh.profile',
        'lead_id',
        string='Hồ sơ CSKH'
    )

    # CUSTOM THÊM MỚI
    # Đếm số lượng Hồ sơ CSKH của Lead/Opportunity
    cskh_profile_count = fields.Integer(
        string='Số hồ sơ CSKH',
        compute='_compute_cskh_profile_count'
    )

    def _compute_cskh_profile_count(self):
        for lead in self:
            lead.cskh_profile_count = len(lead.cskh_profile_ids)