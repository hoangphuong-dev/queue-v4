from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class QueueRoomDistance(models.Model):
    _name = 'queue.room.distance'
    _description = 'Khoảng Cách Giữa Các Phòng'
    _rec_name = 'display_name'

    room_from_id = fields.Many2one('queue.room', string='Từ Phòng', required=True, ondelete='cascade')
    room_to_id = fields.Many2one('queue.room', string='Đến Phòng', required=True, ondelete='cascade')
    distance = fields.Float(string='Khoảng Cách (đơn vị)', required=True, default=1.0,
                            help="Khoảng cách tương đối giữa các phòng, đơn vị tùy chọn (có thể là mét, bước đi, v.v.)")
    travel_time = fields.Float(string='Thời Gian Di Chuyển (phút)',
                               help="Thời gian di chuyển ước tính giữa hai phòng")
    display_name = fields.Char(string='Hiển Thị', compute='_compute_display_name', store=True)

    @api.depends('room_from_id', 'room_to_id', 'distance')
    def _compute_display_name(self):
        for record in self:
            if record.room_from_id and record.room_to_id:
                record.display_name = f"{record.room_from_id.name} → {record.room_to_id.name} ({record.distance})"
            else:
                record.display_name = _("Mới")

    @api.constrains('room_from_id', 'room_to_id')
    def _check_different_rooms(self):
        for record in self:
            if record.room_from_id.id == record.room_to_id.id:
                raise ValidationError(_("Phòng nguồn và phòng đích phải khác nhau!"))

            # Kiểm tra trùng lặp
            existing = self.search([
                ('room_from_id', '=', record.room_from_id.id),
                ('room_to_id', '=', record.room_to_id.id),
                ('id', '!=', record.id)
            ])
            if existing:
                raise ValidationError(_("Đã tồn tại khoảng cách giữa phòng %s và phòng %s!")
                                      % (record.room_from_id.name, record.room_to_id.name))

    @api.model
    def get_distance(self, from_room_id, to_room_id):
        """Lấy khoảng cách giữa hai phòng, bao gồm cả chiều ngược lại"""
        if from_room_id == to_room_id:
            return 0.0

        # Tìm bản ghi trực tiếp
        distance_record = self.search([
            '|',
            '&', ('room_from_id', '=', from_room_id), ('room_to_id', '=', to_room_id),
            '&', ('room_from_id', '=', to_room_id), ('room_to_id', '=', from_room_id)
        ], limit=1)

        if distance_record:
            return distance_record.distance
        else:
            # Giá trị mặc định nếu không tìm thấy
            return 5.0
