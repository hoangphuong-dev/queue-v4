# -*- coding: utf-8 -*-
from odoo import models, fields


class QueuePriority(models.Model):
    _name = 'queue.priority'
    _description = 'Loại Ưu Tiên Hàng Đợi'
    _order = 'priority_level desc'

    name = fields.Char(string='Tên Mức Ưu Tiên', required=True)
    code = fields.Char(string='Mã Ưu Tiên', required=True)
    priority_level = fields.Integer(string='Cấp Độ Ưu Tiên', required=True,
                                    help="Số lớn hơn biểu thị mức ưu tiên cao hơn")
    description = fields.Text(string='Mô Tả')
    color = fields.Integer(string='Màu')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Mã ưu tiên phải là duy nhất!'),
        ('priority_level_uniq', 'unique(priority_level)', 'Cấp độ ưu tiên phải là duy nhất!')
    ]
