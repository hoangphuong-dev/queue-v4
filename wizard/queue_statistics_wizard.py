# -*- coding: utf-8 -*-
from odoo import models, fields
from datetime import timedelta

IR_ACTIONS_REPORT = "ir.actions.report"


class QueueStatisticsWizard(models.TransientModel):
    _name = 'queue.statistics.wizard'
    _description = 'Wizard Báo Cáo Thống Kê Hàng Đợi'

    date_from = fields.Date(string='Từ Ngày', default=lambda self: fields.Date.today() - timedelta(days=30))
    date_to = fields.Date(string='Đến Ngày', default=lambda self: fields.Date.today())
    service_ids = fields.Many2many('queue.service', string='Dịch Vụ')
    room_ids = fields.Many2many('queue.room', string='Phòng')
    report_type = fields.Selection([
        ('summary', 'Tổng Quan'),
        ('detailed', 'Chi Tiết'),
        ('waiting_time', 'Thời Gian Chờ'),
        ('service_time', 'Thời Gian Phục Vụ')
    ], string='Loại Báo Cáo', default='summary')
    group_by = fields.Selection([
        ('day', 'Theo Ngày'),
        ('week', 'Theo Tuần'),
        ('month', 'Theo Tháng'),
        ('service', 'Theo Dịch Vụ'),
        ('room', 'Theo Phòng')
    ], string='Nhóm Theo', default='day')
