# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta, time


class HealthCheckBatch(models.Model):
    _name = 'health.check.batch'
    _description = 'Đợt Khám Sức Khỏe Định Kỳ'

    name = fields.Char(string='Tên Đợt Khám', required=True)
    company_id = fields.Many2one('res.partner', string='Công Ty', domain=[('is_company', '=', True)])
    start_date = fields.Date(string='Ngày Bắt Đầu', required=True)
    end_date = fields.Date(string='Ngày Kết Thúc', required=True)
    patient_ids = fields.Many2many('res.partner', string='Danh Sách Bệnh Nhân', domain=[('is_patient', '=', True)])
    patient_count = fields.Integer(string='Số Lượng Bệnh Nhân', compute='_compute_patient_count')
    token_ids = fields.One2many('queue.token', 'health_check_batch_id', string='Danh Sách Token')
    state = fields.Selection([
        ('draft', 'Dự Thảo'),
        ('planned', 'Đã Lên Kế Hoạch'),
        ('in_progress', 'Đang Tiến Hành'),
        ('completed', 'Hoàn Thành'),
        ('cancelled', 'Đã Hủy')
    ], string='Trạng Thái', default='draft')

    @api.depends('patient_ids')
    def _compute_patient_count(self):
        for record in self:
            record.patient_count = len(record.patient_ids)

    def action_create_reservations(self):
        """Tạo đặt lịch phòng cho đợt khám"""
        self.ensure_one()

        # Lấy danh sách các phòng
        rooms = self.env['queue.room'].search([('state', '=', 'open')])

        # Tạo đặt lịch cho mỗi ngày trong khoảng thời gian
        current_date = self.start_date
        while current_date <= self.end_date:
            # Tạo đặt lịch buổi sáng (7:30 - 11:30)
            morning_start = datetime.combine(current_date, time(7, 30))
            morning_end = datetime.combine(current_date, time(11, 30))

            for room in rooms:
                self.env['queue.room.reservation'].create({
                    'room_id': room.id,
                    'start_time': fields.Datetime.to_string(morning_start),
                    'end_time': fields.Datetime.to_string(morning_end),
                    'service_type': 'health_check',
                    'capacity_percentage': 100
                })

            current_date += timedelta(days=1)

        self.state = 'planned'
        return True
