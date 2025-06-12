# models/queue_coordination_log.py
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class QueueCoordinationLog(models.Model):
    _name = 'queue.coordination.log'
    _description = 'Log Điều Phối Hàng Đợi'
    _order = 'create_date desc'
    _rec_name = 'coordination_summary'
    
    name = fields.Char(string='Mã Log', readonly=True, default=lambda self: _('New'))
    coordination_summary = fields.Char(string='Tóm Tắt', compute='_compute_coordination_summary', store=True)
    
    # Patient and user info
    patient_id = fields.Many2one('res.partner', string='Bệnh Nhân', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Người Thực Hiện', required=True, default=lambda self: self.env.user)
    
    # Coordination type
    coordination_type = fields.Selection([
        ('service_change', 'Đổi Dịch Vụ'),
        ('room_change', 'Đổi Phòng'),
        ('position_change', 'Đổi Vị Trí Trong Phòng')
    ], string='Loại Điều Phối', required=True)
    
    # Service information
    from_service_id = fields.Many2one('queue.service', string='Từ Dịch Vụ', required=True)
    to_service_id = fields.Many2one('queue.service', string='Đến Dịch Vụ', required=True)
    
    # Room information  
    from_room_id = fields.Many2one('queue.room', string='Từ Phòng')
    to_room_id = fields.Many2one('queue.room', string='Đến Phòng')
    
    # Queue information
    old_position = fields.Integer(string='Vị Trí Cũ')
    new_position = fields.Integer(string='Vị Trí Mới')
    
    # Token information
    old_token_id = fields.Many2one('queue.token', string='Token Cũ', ondelete='set null')
    new_token_id = fields.Many2one('queue.token', string='Token Mới', ondelete='set null')
    
    # Additional info
    priority = fields.Integer(string='Mức Ưu Tiên')
    coordination_reason = fields.Text(string='Lý Do Điều Phối')
    coordination_date = fields.Datetime(string='Thời Gian Điều Phối', default=fields.Datetime.now)
    
    @api.depends('patient_id', 'from_service_id', 'to_service_id', 'coordination_type')
    def _compute_coordination_summary(self):
        for log in self:
            if log.coordination_type == 'service_change':
                log.coordination_summary = f"{log.patient_id.name}: {log.from_service_id.name} → {log.to_service_id.name}"
            else:
                log.coordination_summary = f"{log.patient_id.name}: {log.from_room_id.name} → {log.to_room_id.name}"
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('queue.coordination.log') or _('New')
        return super(QueueCoordinationLog, self).create(vals_list)