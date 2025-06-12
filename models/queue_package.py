# -*- coding: utf-8 -*-
from odoo import models, fields


class QueuePackage(models.Model):
    _name = 'queue.package'
    _description = 'Gói Khám Sức Khỏe'

    name = fields.Char(string='Tên Gói', required=True)
    code = fields.Char(string='Mã Gói', required=True)
    description = fields.Text(string='Mô Tả')
    service_ids = fields.Many2many('queue.service', string='Dịch Vụ Bao Gồm')
    active = fields.Boolean(string='Hoạt Động', default=True)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Mã gói phải là duy nhất!')
    ]
