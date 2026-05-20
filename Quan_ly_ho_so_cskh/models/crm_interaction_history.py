from odoo import models, fields, api


class CrmInteractionHistory(models.Model):
    _name = 'crm.interaction.history'
    _description = 'Lịch sử tương tác khách hàng'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'interaction_date desc'

    name = fields.Char(
        string='Mã tương tác',
        required=True,
        copy=False,
        readonly=True,
        default='New'
    )

    lead_id = fields.Many2one(
        'crm.lead',
        string='Cơ hội'
    )

    customer_id = fields.Many2one(
        'res.partner',
        string='Khách hàng',
        required=True
    )

    interaction_type = fields.Selection([
        ('email', 'Email'),
        ('call', 'Cuộc gọi'),
        ('meeting', 'Cuộc họp'),
        ('quotation', 'Báo giá'),
        ('complaint', 'Khiếu nại'),
        ('note', 'Ghi chú'),
    ],
        string='Loại tương tác',
        required=True,
        tracking=True
    )

    interaction_date = fields.Datetime(
        string='Ngày tương tác',
        default=fields.Datetime.now
    )

    content = fields.Text(
        string='Nội dung trao đổi'
    )

    result = fields.Text(
        string='Kết quả làm việc'
    )

    customer_need = fields.Text(
        string='Nhu cầu khách hàng'
    )

    next_action = fields.Text(
        string='Hành động tiếp theo'
    )

    followup_deadline = fields.Datetime(
        string='Hạn follow-up'
    )

    user_id = fields.Many2one(
        'res.users',
        string='Nhân viên phụ trách',
        default=lambda self: self.env.user
    )

    state = fields.Selection([
        ('draft', 'Mới tạo'),
        ('done', 'Đã xử lý'),
        ('cancel', 'Hủy')
    ],
        string='Trạng thái',
        default='draft'
    )

    @api.model
    def create(self, vals):

        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env[
                'ir.sequence'
            ].next_by_code(
                'crm.interaction.history'
            ) or 'New'

        record = super().create(vals)

        # Tự động tạo follow-up activity
        if record.followup_deadline:

            self.env['mail.activity'].create({

                'activity_type_id':
                self.env.ref(
                    'mail.mail_activity_data_todo'
                ).id,

                'summary':
                'Nhắc nhở follow-up khách hàng',

                'note':
                record.next_action or '',

                'date_deadline':
                record.followup_deadline,

                'user_id':
                record.user_id.id,

                'res_model_id':
                self.env['ir.model']._get_id(
                    'crm.interaction.history'
                ),

                'res_id':
                record.id,
            })

        return record

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'