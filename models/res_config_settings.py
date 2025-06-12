# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    queue_auto_balance_interval = fields.Integer(
        string='Tần Suất Cân Bằng Tải (phút)',
        default=10,
        config_parameter='hospital_queue_management.auto_balance_interval'
    )

    queue_overload_threshold = fields.Float(
        string='Ngưỡng Quá Tải (%)',
        default=150.0,
        config_parameter='hospital_queue_management.overload_threshold'
    )

    queue_wait_threshold = fields.Float(
        string='Ngưỡng Thời Gian Chờ (phút)',
        default=30.0,
        config_parameter='hospital_queue_management.wait_threshold'
    )

    queue_max_patients_to_move = fields.Integer(
        string='Số Bệnh Nhân Tối Đa Chuyển Mỗi Lần',
        default=3,
        config_parameter='hospital_queue_management.max_patients_to_move'
    )

    queue_enable_sms = fields.Boolean(
        string='Kích Hoạt Thông Báo SMS',
        default=False,
        config_parameter='hospital_queue_management.enable_sms'
    )

    queue_enable_email = fields.Boolean(
        string='Kích Hoạt Thông Báo Email',
        default=False,
        config_parameter='hospital_queue_management.enable_email'
    )

    queue_sms_template_id = fields.Many2one(
        'sms.template',
        string='Mẫu SMS',
        config_parameter='hospital_queue_management.sms_template_id'
    )

    queue_email_template_id = fields.Many2one(
        'mail.template',
        string='Mẫu Email',
        config_parameter='hospital_queue_management.email_template_id'
    )
