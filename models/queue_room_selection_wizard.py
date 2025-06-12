# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class QueueRoomSelectionWizard(models.TransientModel):
    _name = 'queue.room.selection.wizard'
    _description = 'Wizard Chọn Phòng Điều Phối'
    
    patient_id = fields.Many2one('res.partner', string='Bệnh Nhân', required=True)
    service_id = fields.Many2one('queue.service', string='Dịch Vụ', required=True)
    current_room_id = fields.Many2one('queue.room', string='Phòng Hiện Tại')
    selected_room_id = fields.Many2one('queue.room', string='Phòng Được Chọn', required=True)
    room_line_ids = fields.One2many('queue.room.selection.line', 'wizard_id', string='Danh Sách Phòng')
    # Thêm field coordination_type
    coordination_type = fields.Selection([
        ('room_change', 'Đổi phòng cùng dịch vụ'),
        ('service_room_change', 'Đổi phòng cho dịch vụ')
    ], default='room_change', string='Loại điều phối')
    
    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        
        # Get từ context với prefix 'default_'
        patient_id = self.env.context.get('default_patient_id') or self.env.context.get('patient_id')
        service_id = self.env.context.get('default_service_id') or self.env.context.get('service_id')
        current_room_id = self.env.context.get('default_current_room_id') or self.env.context.get('current_room_id')
        coordination_type = self.env.context.get('default_coordination_type') or self.env.context.get('coordination_type', 'room_change')
        
        if patient_id:
            defaults['patient_id'] = patient_id
        if service_id:
            defaults['service_id'] = service_id
        if current_room_id:
            defaults['current_room_id'] = current_room_id
        defaults['coordination_type'] = coordination_type
            
        return defaults
    
    @api.model
    def create(self, vals):
        wizard = super().create(vals)
        wizard._populate_room_lines()
        return wizard
        
    @api.onchange('service_id')
    def _onchange_service_id(self):
        """Populate room lines when service changes"""
        if self.service_id:
            self._populate_room_lines()
            
    def _populate_room_lines(self):
        """Populate available rooms for the service"""
        self.room_line_ids = [(5, 0, 0)]  # Clear existing lines
        
        if not self.service_id:
            return
            
        # Find all open rooms for this service
        available_rooms = self.env['queue.room'].search([
            ('service_id', '=', self.service_id.id),
            ('state', '=', 'open')
        ])
        
        if not available_rooms:
            return
            
        # Find least loaded room
        least_loaded_room = self._find_least_loaded_room(available_rooms)
        
        # Create lines for each room
        lines = []
        for room in available_rooms:
            queue_info = self._get_room_queue_info(room)
            
            line_vals = {
                'room_id': room.id,
                'waiting_count': queue_info['waiting_count'],
                'estimated_wait_time': queue_info['estimated_wait_time'],
                'is_current': room.id == self.current_room_id.id if self.current_room_id else False,
                'is_recommended': room.id == least_loaded_room.id if least_loaded_room else False,
            }
            lines.append((0, 0, line_vals))
            
        self.room_line_ids = lines
    
    def _find_least_loaded_room(self, rooms):
        """Find room with least load"""
        least_loaded_room = None
        min_load = float('inf')
        
        for room in rooms:
            waiting_count = self.env['queue.token'].search_count([
                ('room_id', '=', room.id),
                ('state', '=', 'waiting')
            ])
            
            load_ratio = waiting_count / room.capacity if room.capacity > 0 else float('inf')
            
            if load_ratio < min_load:
                min_load = load_ratio
                least_loaded_room = room
                
        return least_loaded_room
    
    def _get_room_queue_info(self, room):
        """Get real-time queue info for room"""
        waiting_tokens = self.env['queue.token'].search([
            ('room_id', '=', room.id),
            ('state', '=', 'waiting')
        ])
        
        waiting_count = len(waiting_tokens)
        
        # Calculate estimated wait time
        if waiting_count == 0:
            estimated_wait_time = 0
        else:
            # Simple estimation: count * average service duration
            avg_duration = room.service_id.average_duration or 15  # default 15 minutes
            estimated_wait_time = waiting_count * avg_duration
            
        return {
            'waiting_count': waiting_count,
            'estimated_wait_time': estimated_wait_time
        }
    
    def action_coordinate(self):
        """Thực hiện điều phối chuyển phòng"""
        if not self.selected_room_id:
            raise UserError(_('Vui lòng chọn phòng muốn chuyển đến'))
            
        if self.selected_room_id.id == self.current_room_id.id:
            raise UserError(_('Phòng được chọn giống phòng hiện tại'))
        
        # Xử lý theo coordination_type
        if self.coordination_type == 'service_room_change':
            result = self.patient_id.with_context(
                target_room_id=self.selected_room_id.id,
                target_service_id=self.service_id.id,
                coordination_type='service_room_selection'
            ).action_coordinate_service_room()
        else:
            # Đổi phòng thông thường
            result = self.patient_id.with_context(
                target_room_id=self.selected_room_id.id,
                coordination_type='room_change'
            ).action_coordinate_room()
        
        return result


class QueueRoomSelectionLine(models.TransientModel):
    _name = 'queue.room.selection.line'
    _description = 'Dòng Chọn Phòng'
    
    wizard_id = fields.Many2one('queue.room.selection.wizard', string='Wizard', ondelete='cascade')
    room_id = fields.Many2one('queue.room', string='Phòng', required=True)
    waiting_count = fields.Integer(string='Số Người Chờ')
    estimated_wait_time = fields.Float(string='Thời Gian Chờ Ước Tính (phút)')
    is_current = fields.Boolean(string='Phòng Hiện Tại')
    is_recommended = fields.Boolean(string='Được Đề Xuất')
    
    # Computed fields for UI
    wait_time_color = fields.Selection([
        ('green', 'Xanh'),
        ('orange', 'Cam'),
        ('red', 'Đỏ')
    ], compute='_compute_wait_time_color')
    
    wait_time_text = fields.Char(compute='_compute_wait_time_text')
    
    @api.depends('estimated_wait_time')
    def _compute_wait_time_color(self):
        for line in self:
            if line.estimated_wait_time < 25:
                line.wait_time_color = 'green'
            elif line.estimated_wait_time <= 45:
                line.wait_time_color = 'orange'
            else:
                line.wait_time_color = 'red'
    
    @api.depends('estimated_wait_time')
    def _compute_wait_time_text(self):
        for line in self:
            if line.estimated_wait_time == 0:
                line.wait_time_text = '0 phút'
            else:
                line.wait_time_text = f'{int(line.estimated_wait_time)} phút'