# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date, datetime
import logging
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_patient = fields.Boolean(string='Là Bệnh Nhân', default=False)
    date_of_birth = fields.Date(string='Ngày Sinh')
    age = fields.Integer(string='Tuổi', compute='_compute_age', store=True)
    gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác')
    ], string='Giới Tính')
    is_pregnant = fields.Boolean(string='Mang Thai', default=False)
    is_disabled = fields.Boolean(string='Khuyết Tật', default=False)
    has_urgent_condition = fields.Boolean(string='Tình Trạng Cấp Thiết', default=False)
    is_vip = fields.Boolean(string='VIP', default=False)
    doctor_assigned_priority = fields.Boolean(string='Ưu Tiên Chỉ Định Bác Sĩ', default=False)
    queue_package_id = fields.Many2one('queue.package', string='Gói Khám Sức Khỏe')
    queue_history_ids = fields.One2many('queue.token', 'patient_id', string='Lịch Sử Khám')
    queue_history_count = fields.Integer(string='Số lượng token', compute='_compute_queue_history_count')
    current_service_group_id = fields.Many2one('queue.service.group', string='Nhóm Dịch Vụ Hiện Tại')
    completed_service_ids = fields.Many2many(
        'queue.service',
        'partner_completed_service_rel',
        'partner_id',
        'service_id',
        string='Dịch Vụ Đã Hoàn Thành'
    )
    available_coordination_service_ids = fields.Many2many(
        'queue.service',
        'partner_available_coordination_service_rel',
        'partner_id',
        'service_id',
        string='Dịch Vụ Có Thể Điều Phối',
        compute='_compute_available_coordination_services'
    )
    coordination_service_info = fields.Text(
        string='Thông tin chi tiết dịch vụ điều phối',
        compute='_compute_coordination_service_info',
        store=False  # Không store vì thông tin thay đổi real-time
    )
    
   # Token đang chờ
    current_waiting_token_id = fields.Many2one(
        'queue.token', 
        string='Token đang chờ',
        compute='_compute_current_service_info',
        store=False
    )
    
    # Thông tin dịch vụ tiếp theo
    next_service_name = fields.Char(
        string='Tên dịch vụ tiếp theo',
        compute='_compute_current_service_info'
    )
    next_service_room = fields.Char(
        string='Phòng',
        compute='_compute_current_service_info'
    )
    next_service_position = fields.Integer(
        string='Vị trí',
        compute='_compute_current_service_info'
    )
    next_service_queue_count = fields.Integer(
        string='Số người chờ',
        compute='_compute_current_service_info'
    )
    next_service_wait_time = fields.Float(
        string='Thời gian chờ',
        compute='_compute_current_service_info'
    )
    next_service_token_name = fields.Char(
        string='Mã token',
        compute='_compute_current_service_info'
    )
    
    def action_open_current_service_room_selection(self):
        """Open room selection for current waiting service"""
        self.ensure_one()
        
        if not self.current_waiting_token_id:
            raise UserError(_('Không có dịch vụ đang chờ'))
            
        token = self.current_waiting_token_id
        
        return {
            'name': 'Đổi phòng',
            'type': 'ir.actions.act_window',
            'res_model': 'queue.room.selection.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('hospital_queue_management.view_queue_room_selection_wizard_simple_form').id,
            'target': 'new',
            'context': {
                'default_patient_id': self.id,
                'default_service_id': token.service_id.id,
                'default_current_room_id': token.room_id.id if token.room_id else False,
                'default_coordination_type': 'room_change'
            }
        }
    
    @api.depends('queue_history_ids', 'queue_history_ids.state')
    def _compute_current_service_info(self):
        for partner in self:
            # Reset values
            partner.current_waiting_token_id = False
            partner.next_service_name = False
            partner.next_service_room = False
            partner.next_service_position = 0
            partner.next_service_queue_count = 0
            partner.next_service_wait_time = 0
            partner.next_service_token_name = False
            
            if not partner.is_patient:
                continue
                
            # Tìm token đang waiting
            waiting_token = partner.queue_history_ids.filtered(
                lambda t: t.state == 'waiting'
            )
            
            if waiting_token:
                token = waiting_token[0]
                partner.current_waiting_token_id = token
                partner.next_service_name = token.service_id.name
                partner.next_service_room = token.room_id.name
                partner.next_service_position = token.position
                partner.next_service_token_name = token.name
                
                # Tính số người chờ
                queue_count = self.env['queue.token'].search_count([
                    ('room_id', '=', token.room_id.id),
                    ('state', '=', 'waiting'),
                    ('position', '<', token.position)
                ])
                partner.next_service_queue_count = queue_count
                partner.next_service_wait_time = token.estimated_wait_time

    @api.depends('available_coordination_service_ids')
    def _compute_coordination_service_info(self):
        """Compute thông tin chi tiết cho các dịch vụ có thể điều phối"""
        import json
        
        for partner in self:
            if not partner.available_coordination_service_ids:
                partner.coordination_service_info = '{}'
                continue
                
            info_dict = {}
            for service in partner.available_coordination_service_ids:
                service_info = partner.get_service_coordination_info(service.id)
                info_dict[str(service.id)] = service_info
                
            partner.coordination_service_info = json.dumps(info_dict, ensure_ascii=False)

    @api.depends('queue_package_id', 'completed_service_ids', 'queue_history_ids.state')
    def _compute_available_coordination_services(self):
        """Compute danh sách dịch vụ có thể điều phối"""
        for partner in self:
            if not partner.is_patient or not partner.queue_package_id:
                partner.available_coordination_service_ids = [(6, 0, [])]
                continue
                
            # Check if there's a waiting token
            waiting_tokens = partner.queue_history_ids.filtered(lambda t: t.state == 'waiting')
            if not waiting_tokens:
                partner.available_coordination_service_ids = [(6, 0, [])]
                continue
                
            # Get services chưa hoàn thành trong gói
            package_services = partner.queue_package_id.service_ids
            completed_services = partner.completed_service_ids
            remaining_services = package_services - completed_services
            
            # Loại bỏ service hiện tại đang chờ
            current_service = waiting_tokens[0].service_id
            remaining_services = remaining_services - current_service
            
            # Filter services có phòng khả dụng
            available_service_ids = []
            
            for service in remaining_services:
                service_info = partner.get_service_coordination_info(service.id)
                # Chỉ thêm service nếu có phòng khả dụng
                if service_info.get('available', False):
                    available_service_ids.append(service.id)
                    
            partner.available_coordination_service_ids = [(6, 0, available_service_ids)]
            
    @api.depends('queue_history_ids', 'queue_history_ids.state', 'completed_service_ids', 'queue_package_id',
                 'queue_package_id.service_ids')
    def get_service_coordination_info(self, service_id):
        """Get real-time coordination info for a service"""
        service = self.env['queue.service'].browse(service_id)
        if not service.exists():
            return {'available': False, 'message': 'Dịch vụ không tồn tại'}

        # Get available rooms
        available_rooms = self.env['queue.room'].search([
            ('service_id', '=', service.id),
            ('state', '=', 'open')
        ])

        if not available_rooms:
            return {
                'available': False,
                'message': 'Không có phòng khả dụng',
                'room_count': 0,
                'queue_length': 0,
                'estimated_wait': 0
            }

        # Get least loaded room
        least_loaded_room = self._find_least_loaded_room_for_service(service)

        # Get queue stats for ONLY the recommended room
        if least_loaded_room:
            waiting_tokens = self.env['queue.token'].search([
                ('room_id', '=', least_loaded_room.id),
                ('state', '=', 'waiting')
            ])
            
            room_waiting = len(waiting_tokens)
            
            # Calculate estimated wait time for recommended room only
            if room_waiting > 0:
                total_wait_time = sum(token.estimated_wait_time for token in waiting_tokens)
                avg_wait = total_wait_time / room_waiting
            else:
                avg_wait = 0
        else:
            room_waiting = 0
            avg_wait = 0

        # Determine wait color based on average wait time
        if avg_wait < 25:
            wait_color = 'success'
        elif avg_wait <= 45:
            wait_color = 'warning'
        else:
            wait_color = 'danger'

        return {
            'available': True,
            'service_name': service.name,
            'room_count': len(available_rooms),
            'recommended_room': least_loaded_room.name if least_loaded_room else '',
            'queue_length': room_waiting,  # Chỉ tính cho recommended room
            'estimated_wait': int(avg_wait),  # Chỉ tính cho recommended room
            'wait_color': wait_color
        }

    def _get_room_queue_info(self, room):
        """Lấy thông tin hàng đợi của phòng"""
        if not room:
            return {'waiting_count': 0, 'priority_count': 0}

        # Đếm số token đang chờ trong phòng
        waiting_tokens = self.env['queue.token'].search([
            ('room_id', '=', room.id),
            ('state', '=', 'waiting')
        ])

        # Đếm số token ưu tiên (emergency hoặc priority > 5)
        priority_tokens = waiting_tokens.filtered(
            lambda t: t.emergency or t.priority > 5
        )

        return {
            'waiting_count': len(waiting_tokens),
            'priority_count': len(priority_tokens)
        }

    # Các trường mới cho danh sách bệnh nhân
    patient_category = fields.Selection([
        ('vvip', 'VVIP'),
        ('vip', 'VIP'),
        ('normal', 'KH thường'),
        ('child', 'Trẻ em'),
        ('pregnant', 'Thai phụ'),
        ('elderly', 'Người già'),
        ('nccvcm', 'NCCVCM'),
    ], string='Đối tượng', default='normal')

    patient_id_number = fields.Char(string='PID', help="Patient ID Number")

    # Các trường computed
    exam_count = fields.Char(string='Xét nghiệm', compute='_compute_exam_progress', store=False)
    imaging_count = fields.Char(string='CĐHA', compute='_compute_imaging_progress', store=False)
    specialty_count = fields.Char(string='Chuyên khoa', compute='_compute_specialty_progress', store=False)
    estimated_time = fields.Char(string='Thời gian đợi', compute='_compute_estimated_time', store=False)

    @api.depends('date_of_birth')
    def _compute_age(self):
        """Tính tuổi từ ngày sinh"""
        for partner in self:
            if partner.date_of_birth:
                today = date.today()
                born = partner.date_of_birth
                partner.age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            else:
                partner.age = 0

    @api.depends('queue_history_ids')
    def _compute_queue_history_count(self):
        """Đếm số lượng token đã cấp cho bệnh nhân"""
        for partner in self:
            partner.queue_history_count = len(partner.queue_history_ids)

    def _compute_exam_progress(self):
        """Tính tiến độ xét nghiệm"""
        for partner in self:
            if partner.is_patient and partner.queue_history_ids:
                exam_tokens = partner.queue_history_ids.filtered(
                    lambda t: t.service_id.service_type == 'lab'
                )
                completed = exam_tokens.filtered(lambda t: t.state == 'completed')
                total = len(exam_tokens)
                completed_count = len(completed)
                partner.exam_count = f"{completed_count}/{total}" if total > 0 else "1/3"
            else:
                partner.exam_count = "1/3"

    def _compute_imaging_progress(self):
        """Tính tiến độ chẩn đoán hình ảnh"""
        for partner in self:
            if partner.is_patient and partner.queue_history_ids:
                imaging_tokens = partner.queue_history_ids.filtered(
                    lambda t: t.service_id.service_type == 'imaging'
                )
                completed = imaging_tokens.filtered(lambda t: t.state == 'completed')
                total = len(imaging_tokens)
                completed_count = len(completed)
                partner.imaging_count = f"{completed_count}/{total}" if total > 0 else "1/7"
            else:
                partner.imaging_count = "1/7"

    def _compute_specialty_progress(self):
        """Tính tiến độ chuyên khoa"""
        for partner in self:
            if partner.is_patient and partner.queue_history_ids:
                specialty_tokens = partner.queue_history_ids.filtered(
                    lambda t: t.service_id.service_type in ['consultation', 'specialty']
                )
                completed = specialty_tokens.filtered(lambda t: t.state == 'completed')
                total = len(specialty_tokens)
                completed_count = len(completed)
                partner.specialty_count = f"{completed_count}/{total}" if total > 0 else "2/6"
            else:
                partner.specialty_count = "2/6"

    def action_back(self):
        """Quay lại danh sách bệnh nhân"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Danh sách bệnh nhân',
            'res_model': 'res.partner',
            'view_mode': 'kanban,list',
            'domain': [('is_patient', '=', True)],
            'context': {'default_is_patient': True},
            'target': 'current',
        }

    def _compute_estimated_time(self):
        """Tính thời gian đợi ước tính"""
        for partner in self:
            if partner.is_patient and partner.queue_history_ids:
                waiting_token = partner.queue_history_ids.filtered(
                    lambda t: t.state == 'waiting'
                ).sorted('estimated_wait_time')

                if waiting_token:
                    time_minutes = waiting_token[0].estimated_wait_time
                    hours = int(time_minutes // 60)
                    minutes = int(time_minutes % 60)
                    if hours > 0:
                        partner.estimated_time = f"{hours} giờ {minutes} phút"
                    else:
                        partner.estimated_time = f"{minutes} phút"
                else:
                    partner.estimated_time = "1 giờ 12 phút"
            else:
                partner.estimated_time = "1 giờ 12 phút"

    def action_swap_to_service(self):
        """
        Điều phối: Chuyển từ dịch vụ đang chờ sang dịch vụ mới được chọn
        Context cần có: target_service_id
        """
        # Get target service from context (đảm bảo đúng tên biến)
        target_service_id = self.env.context.get('target_service_id')
        if not target_service_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi',
                    'message': 'Không xác định được dịch vụ cần chuyển',
                    'type': 'danger',
                    'sticky': False
                }
            }

        try:
            # Step 1: Validation
            validation_result = self._validate_service_coordination_request(target_service_id)
            if validation_result.get('error'):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Lỗi Điều Phối',
                        'message': validation_result.get('message', 'Lỗi không xác định'),
                        'type': 'danger',
                        'sticky': False
                    }
                }

            # Step 2: Get current waiting token and target service
            current_token = validation_result['current_token']
            target_service = validation_result['target_service']

            # Step 3: Find least loaded room for target service
            target_room = self._find_least_loaded_room_for_service(target_service)
            if not target_room:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Lỗi',
                        'message': f'Không có phòng khả dụng cho dịch vụ {target_service.name}',
                        'type': 'danger',
                        'sticky': False
                    }
                }

            # Step 4: Create new token (will auto go to end of queue)
            new_token = self._create_coordination_token(current_token, target_service, target_room)

            # Step 5: Log coordination
            self._log_coordination(
                current_token=current_token,
                new_token=new_token,
                coordination_type='service_change',
                reason=f'Điều phối từ dịch vụ {current_token.service_id.name} sang {target_service.name}'
            )

            # Step 6: Delete old token
            current_token.unlink()

            # Step 7: Refresh computed fields 
            self.invalidate_recordset(['available_coordination_service_ids'])

            return {
                'type': 'ir.actions.client',
                'tag': 'reload',  # This will reload the current view
                'params': {
                    'menu_id': self.env.context.get('menu_id'),
                },
                'context': self.env.context,
            }

        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi Hệ Thống',
                    'message': f'Không thể thực hiện điều phối: {str(e)}',
                    'type': 'danger',
                    'sticky': True
                }
            }

    def action_coordinate_room(self):
        """
        Thực hiện điều phối chuyển phòng cùng dịch vụ
        Context cần có: target_room_id
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        _logger.info("=== ROOM COORDINATION ===")
        _logger.info("Context: %s", self.env.context)
        
        # Get target room from context
        target_room_id = self.env.context.get('target_room_id')
        if not target_room_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi',
                    'message': 'Không xác định được phòng cần chuyển',
                    'type': 'danger'
                }
            }
        
        try:
            # Validate request
            validation_result = self._validate_room_coordination_request(target_room_id)
            if validation_result.get('error'):
                return validation_result
                
            current_token = validation_result['current_token']
            target_room = validation_result['target_room']
            
            # Create new token in target room
            new_token = self._create_coordination_token(
                current_token,
                current_token.service_id,  # Same service
                target_room
            )
            
            # Log coordination
            self._log_coordination(
                current_token=current_token,
                new_token=new_token,
                coordination_type='room_change',
                reason=f'Đổi phòng từ {current_token.room_id.name} sang {target_room.name}'
            )
            
            # Delete old token
            current_token.unlink()
            
            # Show success message and reload
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
                'params': {
                    'menu_id': self.env.context.get('menu_id'),
                }
            }
            
        except Exception as e:
            _logger.error("Room coordination failed: %s", str(e))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi',
                    'message': str(e),
                    'type': 'danger'
                }
            }

    def _validate_service_coordination_request(self, target_service_id):
        """Validate service coordination request"""

        # Check if patient
        if not self.is_patient:
            return {
                'error': True,
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'title': 'Lỗi', 'message': 'Đây không phải bệnh nhân', 'type': 'danger'}
            }

        # Find current waiting token
        current_waiting_tokens = self.queue_history_ids.filtered(lambda t: t.state == 'waiting')
        if not current_waiting_tokens:
            return {
                'error': True,
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'title': 'Thông báo', 'message': 'Không có dịch vụ đang chờ', 'type': 'warning'}
            }

        current_token = current_waiting_tokens[0]

        # Validate target service
        target_service = self.env['queue.service'].browse(target_service_id)
        if not target_service.exists():
            return {
                'error': True,
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'title': 'Lỗi', 'message': 'Dịch vụ không tồn tại', 'type': 'danger'}
            }

        # Check if service in package
        if self.queue_package_id and target_service not in self.queue_package_id.service_ids:
            return {
                'error': True,
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'title': 'Lỗi', 'message': 'Dịch vụ không có trong gói khám', 'type': 'danger'}
            }

        # Check if already completed
        if target_service in self.completed_service_ids:
            return {
                'error': True,
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'title': 'Lỗi', 'message': 'Dịch vụ đã được thực hiện', 'type': 'danger'}
            }

        # Check if same service
        if current_token.service_id.id == target_service.id:
            return {
                'error': True,
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'title': 'Thông báo', 'message': 'Đã đang trong dịch vụ này rồi', 'type': 'info'}
            }

        return {
            'error': False,
            'current_token': current_token,
            'target_service': target_service
        }

    def _validate_room_coordination_request(self, target_room_id):
        """Validate room coordination request"""

        # Find current waiting token
        current_waiting_tokens = self.queue_history_ids.filtered(lambda t: t.state == 'waiting')
        if not current_waiting_tokens:
            return {
                'error': True,
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'title': 'Thông báo', 'message': 'Không có dịch vụ đang chờ', 'type': 'warning'}
            }

        current_token = current_waiting_tokens[0]

        # Validate target room
        target_room = self.env['queue.room'].browse(target_room_id)
        if not target_room.exists():
            return {
                'error': True,
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'title': 'Lỗi', 'message': 'Phòng không tồn tại', 'type': 'danger'}
            }

        # Check if room is open
        if target_room.state != 'open':
            return {
                'error': True,
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'title': 'Lỗi', 'message': 'Phòng đã đóng hoặc đang bảo trì', 'type': 'danger'}
            }

        # Check if room supports current service
        if target_room.service_id.id != current_token.service_id.id:
            return {
                'error': True,
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'title': 'Lỗi', 'message': 'Phòng không hỗ trợ dịch vụ hiện tại', 'type': 'danger'}
            }

        return {
            'error': False,
            'current_token': current_token,
            'target_room': target_room
        }

    def _find_least_loaded_room_for_service(self, service):
        """Find least loaded room for service"""
        available_rooms = self.env['queue.room'].search([
            ('service_id', '=', service.id),
            ('state', '=', 'open')
        ])

        if not available_rooms:
            return False

        least_loaded_room = None
        min_load = float('inf')

        for room in available_rooms:
            waiting_count = self.env['queue.token'].search_count([
                ('room_id', '=', room.id),
                ('state', '=', 'waiting')
            ])

            load_ratio = waiting_count / room.capacity if room.capacity > 0 else float('inf')

            if load_ratio < min_load:
                min_load = load_ratio
                least_loaded_room = room

        return least_loaded_room

    def _create_coordination_token(self, current_token, target_service, target_room):
        """Create new token for coordination - go to end of queue"""
        
        # Calculate position at END of queue (không kế thừa position cũ)
        existing_tokens = self.env['queue.token'].search([
            ('room_id', '=', target_room.id),
            ('state', '=', 'waiting')
        ], order='position desc')
        
        # Lấy position cuối cùng + 1
        if existing_tokens:
            new_position = existing_tokens[0].position + 1
        else:
            new_position = 1
        
        # Create new token vals
        new_token_vals = {
            'patient_id': self.id,
            'service_id': target_service.id,
            'room_id': target_room.id,
            'position': new_position,  # Vào cuối hàng
            'priority': current_token.priority,  # Vẫn giữ priority
            'priority_id': current_token.priority_id.id if current_token.priority_id else False,
            'emergency': current_token.emergency,
            'package_id': current_token.package_id.id if current_token.package_id else False,
            'service_type': current_token.service_type,
            'health_check_batch_id': current_token.health_check_batch_id.id if current_token.health_check_batch_id else False,
            'state': 'waiting',
            'notes': f"Điều phối từ {current_token.service_id.name} lúc {fields.Datetime.now().strftime('%H:%M')}"
        }
        
        # Create token với context skip auto assignment
        new_token = self.env['queue.token'].with_context(skip_auto_assignment=True).create(new_token_vals)
        
        return new_token

    def _log_coordination(self, current_token, new_token, coordination_type, reason):
        """Log coordination activity"""
        log_vals = {
            'patient_id': self.id,
            'coordination_type': coordination_type,
            'from_service_id': current_token.service_id.id,
            'to_service_id': new_token.service_id.id,
            'from_room_id': current_token.room_id.id if current_token.room_id else False,
            'to_room_id': new_token.room_id.id,
            'old_position': current_token.position,
            'new_position': new_token.position,
            'old_token_id': current_token.id,
            'new_token_id': new_token.id,
            'priority': new_token.priority,
            'coordination_reason': reason
        }

        self.env['queue.coordination.log'].create(log_vals)

    def action_coordinate_service_room(self):
        """
        Điều phối cho dịch vụ với phòng được chọn
        Được gọi khi chọn dịch vụ từ danh sách available services và đã chọn phòng
        Context cần: target_service_id, target_room_id
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        target_service_id = self.env.context.get('target_service_id')
        target_room_id = self.env.context.get('target_room_id')
        
        if not target_service_id or not target_room_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi',
                    'message': 'Thiếu thông tin dịch vụ hoặc phòng',
                    'type': 'danger'
                }
            }
        
        try:
            target_service = self.env['queue.service'].browse(target_service_id)
            target_room = self.env['queue.room'].browse(target_room_id)
            
            if not target_service.exists() or not target_room.exists():
                raise UserError(_('Dịch vụ hoặc phòng không tồn tại'))
                
            # Check if room supports service
            if target_room.service_id.id != target_service.id:
                raise UserError(_('Phòng không hỗ trợ dịch vụ này'))
                
            # Find current waiting token for this service (if any)
            current_token = self.queue_history_ids.filtered(
                lambda t: t.state == 'waiting' and t.service_id.id == target_service_id
            )
            
            if current_token:
                # Already has token for this service - just change room
                old_room = current_token.room_id
                
                # Create new token in new room
                new_token = self._create_coordination_token(
                    current_token,
                    target_service,
                    target_room
                )
                
                # Log coordination
                self._log_coordination(
                    current_token=current_token,
                    new_token=new_token,
                    coordination_type='room_change',
                    reason=f'Đổi phòng từ {old_room.name} sang {target_room.name}'
                )
                
                # Delete old token
                current_token.unlink()
                
                message = f'Đã chuyển từ {old_room.name} sang {target_room.name}'
            else:
                # No current token - create new one
                new_token = self.env['queue.token'].with_context(
                    skip_auto_assignment=True
                ).create({
                    'patient_id': self.id,
                    'service_id': target_service.id,
                    'room_id': target_room.id,
                    'state': 'waiting',
                    'service_type': self.env.context.get('service_type', 'regular'),
                    'notes': f'Tạo mới qua tùy chỉnh phòng'
                })
                
                message = f'Đã tạo token mới tại {target_room.name}'
            
            # Refresh computed fields
            self.invalidate_recordset(['available_coordination_service_ids'])
            
            return {
                'type': 'ir.actions.client', 
                'tag': 'reload',
                'params': {
                    'menu_id': self.env.context.get('menu_id'),
                }
            }
            
        except Exception as e:
            _logger.error("Service room coordination failed: %s", str(e))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi',
                    'message': str(e),
                    'type': 'danger'
                }
            }