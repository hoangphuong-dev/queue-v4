# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class QueueRoomReservation(models.Model):
    _name = 'queue.room.reservation'
    _description = 'Đặt Lịch Phòng Khám'
    _order = 'start_time asc'

    name = fields.Char(string='Tên', compute='_compute_name')
    room_id = fields.Many2one('queue.room', string='Phòng', required=True)
    start_time = fields.Datetime(string='Thời Gian Bắt Đầu', required=True)
    end_time = fields.Datetime(string='Thời Gian Kết Thúc', required=True)
    service_type = fields.Selection([
        ('health_check', 'Khám Sức Khỏe Định Kỳ'),
        ('insurance', 'Khám Bảo Hiểm'),
        ('emergency', 'Cấp Cứu'),
        ('regular', 'Khám Thường'),
        ('all', 'Tất Cả Dịch Vụ'),
    ], string='Loại Dịch Vụ', required=True, default='all')
    capacity_percentage = fields.Integer(string='Phần Trăm Công Suất', default=100)
    active = fields.Boolean(string='Hoạt Động', default=True)

    @api.depends('room_id', 'start_time', 'end_time')
    def _compute_name(self):
        for record in self:
            if record.room_id and record.start_time and record.end_time:
                start = record.start_time.strftime('%H:%M')
                end = record.end_time.strftime('%H:%M')
                record.name = f"{record.room_id.name}: {start} - {end}"
            else:
                record.name = _("Đặt Lịch Mới")

    @api.constrains('start_time', 'end_time')
    def _check_times(self):
        for record in self:
            if record.start_time >= record.end_time:
                raise ValidationError(_("Thời gian kết thúc phải sau thời gian bắt đầu"))

    @api.constrains('capacity_percentage')
    def _check_capacity(self):
        for record in self:
            if record.capacity_percentage <= 0 or record.capacity_percentage > 100:
                raise ValidationError(_("Phần trăm công suất phải từ 1 đến 100"))
