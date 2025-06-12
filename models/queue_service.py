# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

QUEUE_PACKAGE = "queue.package"
QUEUE_SERVICE = "queue.service"
IR_ACTIONS_CLIENT = "ir.actions.client"


class QueueService(models.Model):
    _name = QUEUE_SERVICE
    _description = 'Dịch Vụ Y Tế'

    name = fields.Char(string='Tên Dịch Vụ', required=True)
    code = fields.Char(string='Mã Dịch Vụ', required=True)
    sequence = fields.Integer(string='Thứ Tự', default=10)
    active = fields.Boolean(string='Hoạt Động', default=True)
    service_type = fields.Selection([
        ('registration', 'Đăng Ký'),
        ('vitals', 'Dấu Hiệu Sinh Tồn'),
        ('lab', 'Xét Nghiệm'),
        ('imaging', 'Chẩn Đoán Hình Ảnh'),
        ('consultation', 'Khám Bệnh'),
        ('specialty', 'Khám Chuyên Khoa'),
        ('other', 'Khác')
    ], string='Loại Dịch Vụ', required=True)
    description = fields.Text(string='Mô Tả')
    average_duration = fields.Float(string='Thời Gian Trung Bình của dịch vụ (phút)', default=10.0)
    duration_count = fields.Integer(string='Số Lượt Tính Thời Gian', default=0)
    rooms_ids = fields.One2many('queue.room', 'service_id', string='Phòng Phục Vụ')

    available_rooms_count = fields.Integer(
        string='Số phòng đang mở',
        compute='_compute_coordination_display_info'
    )
    suggested_room_name = fields.Char(
        string='Phòng đề xuất',
        compute='_compute_coordination_display_info'
    )
    waiting_queue_count = fields.Integer(
        string='Số người chờ',
        compute='_compute_coordination_display_info'
    )
    estimated_wait_time = fields.Float(
        string='Thời gian TB phòng đề xuất',
        compute='_compute_coordination_display_info'
    )
    
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Mã dịch vụ phải là duy nhất!')
    ]

    @api.depends('rooms_ids.state')
    def _compute_coordination_display_info(self):
        """Compute coordination display info for list view"""
        for service in self:
            # Tìm patient từ available_coordination_service_ids relationship
            patient = self.env['res.partner'].search([
                ('available_coordination_service_ids', 'in', service.id),
                ('is_patient', '=', True)
            ], limit=1)
            
            if patient:
                service_info = patient.get_service_coordination_info(service.id)
                
                if service_info.get('available', False):
                    service.available_rooms_count = len(service.rooms_ids.filtered(lambda r: r.state == 'open'))
                    service.suggested_room_name = service_info.get('recommended_room', '')
                    service.waiting_queue_count = service_info.get('queue_length', 0)
                    service.estimated_wait_time = service_info.get('estimated_wait', 0)
                else:
                    service.available_rooms_count = 0
                    service.suggested_room_name = 'Không có phòng khả dụng'
                    service.waiting_queue_count = 666666
                    service.estimated_wait_time = 0.0
            else:
                # Default values when no patient found
                open_rooms = service.rooms_ids.filtered(lambda r: r.state == 'open')
                service.available_rooms_count = len(open_rooms)
                service.suggested_room_name = open_rooms[0].name if open_rooms else 'Không có'
                service.waiting_queue_count = 999999
                service.estimated_wait_time = 0.0

    def _update_average_duration(self, duration):
        """
        Cập nhật thời gian trung bình của dịch vụ

        Tham số:
            duration (float): Thời gian thực tế của lần phục vụ mới (phút)
        """
        for service in self:
            current_avg = service.average_duration
            current_count = service.duration_count

            # Tính trung bình cộng theo công thức: ((avg_cũ * số_lượt_cũ) + giá_trị_mới) / (số_lượt_cũ + 1)
            new_count = current_count + 1
            new_avg = ((current_avg * current_count) + duration) / new_count

            service.write({
                'average_duration': new_avg,
                'duration_count': new_count
            })

class QueueServiceGroupRoute(models.Model):
    _name = 'queue.service.group.route'
    _description = 'Tuyến Đường Nhóm Dịch Vụ'

    name = fields.Char(string='Tên Tuyến', compute='_compute_name', store=True)
    group_from_id = fields.Many2one('queue.service.group', string='Từ Nhóm Dịch Vụ', required=True)
    group_to_id = fields.Many2one('queue.service.group', string='Đến Nhóm Dịch Vụ', required=True)
    condition = fields.Text(string='Điều Kiện Chuyển')
    sequence = fields.Integer(string='Độ Ưu Tiên', default=10)
    package_id = fields.Many2one(QUEUE_PACKAGE, string='Gói Dịch Vụ Cụ Thể')

    @api.depends('group_from_id', 'group_to_id')
    def _compute_name(self):
        for route in self:
            if route.group_from_id and route.group_to_id:
                route.name = f"{route.group_from_id.name} → {route.group_to_id.name}"
            else:
                route.name = _("Tuyến Nhóm Mới")

    @api.model
    def create_or_update_route(self, from_group_id, to_group_id):
        """
        Tạo hoặc cập nhật tuyến đường khi kéo thả

        Args:
            from_group_id: ID của nhóm nguồn
            to_group_id: ID của nhóm đích

        Returns:
            dict: Thông tin về tuyến đường đã tạo hoặc cập nhật
        """
        # Kiểm tra xem tuyến đường này đã tồn tại chưa
        existing_route = self.search([
            ('group_from_id', '=', from_group_id),
            ('group_to_id', '=', to_group_id)
        ], limit=1)

        if existing_route:
            # Nếu đã tồn tại, cập nhật sequence (sắp xếp lại ưu tiên)
            existing_route.sequence = 10
            return {
                'type': IR_ACTIONS_CLIENT,
                'tag': 'display_notification',
                'params': {
                    'title': _('Thành công'),
                    'message': _('Tuyến đường đã được cập nhật'),
                    'sticky': False,
                    'type': 'success',
                }
            }
        else:
            # Kiểm tra xem có đang tạo vòng lặp không
            if self._check_route_loop(from_group_id, to_group_id):
                return {
                    'type': IR_ACTIONS_CLIENT,
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Cảnh báo'),
                        'message': _('Không thể tạo tuyến đường vì sẽ tạo ra vòng lặp!'),
                        'sticky': True,
                        'type': 'warning',
                    }
                }

            # Tạo tuyến đường mới
            self.create({
                'group_from_id': from_group_id,
                'group_to_id': to_group_id,
                'sequence': 10,
            })

            return {
                'type': IR_ACTIONS_CLIENT,
                'tag': 'display_notification',
                'params': {
                    'title': _('Thành công'),
                    'message': _('Tuyến đường mới đã được tạo'),
                    'sticky': False,
                    'type': 'success',
                }
            }

    def _check_route_loop(self, from_group_id, to_group_id):
        """
        Kiểm tra xem việc tạo tuyến đường này có tạo vòng lặp không

        Args:
            from_group_id: ID của nhóm nguồn
            to_group_id: ID của nhóm đích

        Returns:
            bool: True nếu tạo vòng lặp, False nếu không
        """
        # Kiểm tra nếu đã có tuyến đường từ to_group quay lại from_group
        return bool(self.search([
            ('group_from_id', '=', to_group_id),
            ('group_to_id', '=', from_group_id)
        ], limit=1))

    @api.model
    def get_route_visualization_data(self):
        """
        Lấy dữ liệu để hiển thị trực quan tuyến đường trong giao diện

        Returns:
            list: Danh sách các tuyến đường dạng dữ liệu đồ họa
        """
        routes = self.search([])
        result = []

        for route in routes:
            result.append({
                'id': route.id,
                'from_id': route.group_from_id.id,
                'from_name': route.group_from_id.name,
                'to_id': route.group_to_id.id,
                'to_name': route.group_to_id.name,
                'package_id': route.package_id.id if route.package_id else False,
                'package_name': route.package_id.name if route.package_id else _('Tất cả'),
            })

        return result


class QueueServiceRoute(models.Model):
    """
    Model này định nghĩa các tuyến đường (route) giữa các dịch vụ
    Ví dụ: Sau khi Đăng Ký -> đi tới Đo Dấu Hiệu Sinh Tồn -> đi tới Xét Nghiệm...
    """
    _name = 'queue.service.route'
    _description = 'Tuyến Đường Dịch Vụ'

    name = fields.Char(string='Tên Tuyến', compute='_compute_name', store=True)
    service_from_id = fields.Many2one(QUEUE_SERVICE, string='Từ Dịch Vụ', required=True)
    service_to_id = fields.Many2one(QUEUE_SERVICE, string='Đến Dịch Vụ', required=True)
    condition = fields.Text(string='Điều Kiện Chuyển',
                            help="Biểu thức Python để xác định liệu tuyến đường này có nên được sử dụng không")
    sequence = fields.Integer(string='Độ Ưu Tiên', default=10,
                              help="Số thấp hơn có độ ưu tiên cao hơn khi có nhiều tuyến có thể áp dụng")
    package_id = fields.Many2one(QUEUE_PACKAGE, string='Gói Dịch Vụ Cụ Thể',
                                 help="Nếu được đặt, tuyến đường này chỉ áp dụng cho gói dịch vụ này")

    @api.depends('service_from_id', 'service_to_id')
    def _compute_name(self):
        """Tạo tên tuyến đường từ tên các dịch vụ liên quan"""
        for route in self:
            if route.service_from_id and route.service_to_id:
                route.name = f"{route.service_from_id.name} → {route.service_to_id.name}"
            else:
                route.name = _("Tuyến Mới")
