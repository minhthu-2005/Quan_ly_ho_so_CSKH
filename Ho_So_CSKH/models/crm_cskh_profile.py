from odoo import models, fields, api, _


class CrmCskhProfile(models.Model):
    # CUSTOM THÊM MỚI
    # Tạo model quản lý Hồ sơ CSKH
    _name = 'crm.cskh.profile'
    _description = 'Hồ sơ chăm sóc khách hàng'

    # KẾ THỪA MODULE MAIL
    # mail.thread, mail.activity.mixin
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _order = 'interaction_date desc, id desc'

    # CUSTOM THÊM MỚI
    # Sinh mã Hồ sơ CSKH tự động
    name = fields.Char(
        string='Mã hồ sơ CSKH',
        required=True,
        copy=False,
        readonly=True,
        default='New'
    )

    # KẾ THỪA MODULE CRM
    # Model crm.lead
    #
    # CUSTOM THÊM MỚI
    # Liên kết Hồ sơ CSKH với Lead/Opportunity
    lead_id = fields.Many2one(
        'crm.lead',
        string='Lead/Opportunity',
        required=True,
        tracking=True,
        ondelete='cascade'
    )

    # KẾ THỪA MODULE CRM
    # Model res.partner
    #
    # CUSTOM THÊM MỚI
    # Lấy thông tin khách hàng từ Lead/Opportunity
    customer_id = fields.Many2one(
        'res.partner',
        string='Khách hàng',
        related='lead_id.partner_id',
        store=True,
        readonly=True
    )

    # CUSTOM THÊM MỚI
    # Lưu Sales Owner phụ trách Hồ sơ CSKH
    user_id = fields.Many2one(
        'res.users',
        string='Sales Owner',
        default=lambda self: self.env.user,
        tracking=True
    )

    # CUSTOM THÊM MỚI
    # Phân loại tương tác với khách hàng
    interaction_type = fields.Selection([
        ('email', 'Email'),
        ('call', 'Cuộc gọi'),
        ('meeting', 'Meeting'),
        ('quotation', 'Báo giá'),
        ('complaint', 'Complaint'),
        ('note', 'Note trao đổi'),
    ], string='Loại tương tác', required=True, tracking=True)

    # CUSTOM THÊM MỚI
    # Lưu thời gian phát sinh tương tác
    interaction_date = fields.Datetime(
        string='Thời gian tương tác',
        default=fields.Datetime.now,
        required=True,
        tracking=True
    )

    # CUSTOM THÊM MỚI
    # Lưu nội dung trao đổi với khách hàng
    content = fields.Text(
        string='Nội dung trao đổi',
        tracking=True
    )

    # CUSTOM THÊM MỚI
    # Lưu kết quả làm việc sau tương tác
    result = fields.Text(
        string='Kết quả làm việc',
        tracking=True
    )

    # CUSTOM THÊM MỚI
    # Lưu nhu cầu khách hàng
    customer_need = fields.Text(
        string='Nhu cầu khách hàng',
        tracking=True
    )

    # CUSTOM THÊM MỚI
    # Lưu hành động chăm sóc tiếp theo
    next_action = fields.Char(
        string='Next Action',
        tracking=True
    )

    # CUSTOM THÊM MỚI
    # Lưu deadline follow-up khách hàng
    followup_deadline = fields.Date(
        string='Deadline Follow-up',
        tracking=True
    )

    # CUSTOM THÊM MỚI
    # Quản lý trạng thái Hồ sơ CSKH
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('pending', 'Cần follow-up'),
        ('done', 'Hoàn thành'),
        ('cancel', 'Hủy'),
    ], string='Trạng thái', default='draft', tracking=True)

    # CUSTOM THÊM MỚI
    # Kiểm tra Hồ sơ CSKH quá hạn follow-up
    is_overdue = fields.Boolean(
        string='Quá hạn',
        compute='_compute_is_overdue'
    )

    @api.depends('followup_deadline', 'state')
    def _compute_is_overdue(self):
        today = fields.Date.today()
        for record in self:
            record.is_overdue = (
                record.followup_deadline
                and record.followup_deadline < today
                and record.state not in ['done', 'cancel']
            )

    @api.model_create_multi
    def create(self, vals_list):
        # CUSTOM THÊM MỚI
        # Sinh mã Hồ sơ CSKH bằng sequence
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'crm.cskh.profile'
                ) or 'New'

        records = super().create(vals_list)

        for record in records:
            record._create_followup_activity()
            record._post_cskh_message()
            record._send_automated_email()

        return records

    def write(self, vals):
        result = super().write(vals)

        for record in self:
            # CUSTOM THÊM MỚI
            # Tạo activity khi cập nhật next action hoặc deadline follow-up
            if 'followup_deadline' in vals or 'next_action' in vals:
                record._create_followup_activity()

        return result

    def _create_followup_activity(self):
        # KẾ THỪA MODULE MAIL
        # Model mail.activity
        #
        # CUSTOM THÊM MỚI
        # Tạo reminder follow-up cho Sales
        for record in self:
            if not record.followup_deadline or not record.next_action:
                continue

            self.env['mail.activity'].create({
                'activity_type_id': self.env.ref(
                    'mail.mail_activity_data_todo'
                ).id,
                'summary': 'Follow-up Hồ sơ CSKH',
                'note': record.next_action,
                'date_deadline': record.followup_deadline,
                'user_id': record.user_id.id,
                'res_model_id': self.env['ir.model']._get_id(
                    'crm.cskh.profile'
                ),
                'res_id': record.id,
            })

            record.state = 'pending'

    def _post_cskh_message(self):
        # KẾ THỪA MODULE MAIL
        # message_post của mail.thread
        #
        # CUSTOM THÊM MỚI
        # Ghi log Hồ sơ CSKH vào chatter
        for record in self:
            record.message_post(
                body=_(
                    'Đã cập nhật Hồ sơ CSKH.<br/>'
                    '<b>Loại tương tác:</b> %s<br/>'
                    '<b>Nội dung:</b> %s<br/>'
                    '<b>Next Action:</b> %s<br/>'
                    '<b>Deadline:</b> %s'
                ) % (
                    record.interaction_type,
                    record.content or '',
                    record.next_action or '',
                    record.followup_deadline or ''
                )
            )

            if record.lead_id:
                record.lead_id.message_post(
                    body=_(
                        'Đã cập nhật Hồ sơ CSKH: <b>%s</b>'
                    ) % record.name
                )

    def _send_automated_email(self):
        # KẾ THỪA MODULE MAIL
        # Model mail.template
        #
        # CUSTOM THÊM MỚI
        # Gửi email tự động khi loại tương tác là Complaint
        for record in self:
            if record.interaction_type != 'complaint':
                continue

            template = self.env.ref(
                'Quan_ly_ho_so_cskh.email_template_complaint_received',
                raise_if_not_found=False
            )

            if template and record.customer_id.email:
                template.send_mail(record.id, force_send=True)

    def action_done(self):
        # CUSTOM THÊM MỚI
        # Button chuyển Hồ sơ CSKH sang trạng thái Hoàn thành
        for record in self:
            record.state = 'done'

    def action_cancel(self):
        # CUSTOM THÊM MỚI
        # Button chuyển Hồ sơ CSKH sang trạng thái Hủy
        for record in self:
            record.state = 'cancel'

    def _cron_crm_update_reminder(self):
        # CUSTOM THÊM MỚI
        # Cron job nhắc cập nhật Hồ sơ CSKH quá hạn
        today = fields.Date.today()

        records = self.search([
            ('followup_deadline', '<', today),
            ('state', 'not in', ['done', 'cancel']),
        ])

        for record in records:
            record.message_post(
                body='Hồ sơ CSKH đã quá hạn follow-up. Sales cần cập nhật kết quả chăm sóc khách hàng.'
            )

            self.env['mail.activity'].create({
                'activity_type_id': self.env.ref(
                    'mail.mail_activity_data_todo'
                ).id,
                'summary': 'Nhắc cập nhật Hồ sơ CSKH',
                'note': 'Vui lòng cập nhật follow-up khách hàng.',
                'date_deadline': today,
                'user_id': record.user_id.id,
                'res_model_id': self.env['ir.model']._get_id(
                    'crm.cskh.profile'
                ),
                'res_id': record.id,
            })