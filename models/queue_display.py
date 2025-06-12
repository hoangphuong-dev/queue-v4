# -*- coding: utf-8 -*-
from odoo import models, fields


class QueueDisplay(models.Model):
    _name = 'queue.display'
    _description = 'Màn Hình Hiển Thị Hàng Đợi'

    name = fields.Char(string='Tên Màn Hình', required=True)
    location = fields.Char(string='Vị Trí')
    room_ids = fields.Many2many('queue.room', string='Phòng Hiển Thị')
    display_count = fields.Integer(string='Số Lượng Token Hiển Thị', default=10)
    refresh_interval = fields.Integer(string='Tần Suất Làm Mới (giây)', default=10)
    show_estimated_time = fields.Boolean(string='Hiển Thị Thời Gian Chờ Ước Tính', default=True)
    active = fields.Boolean(string='Hoạt Động', default=True)

    def get_display_data(self):
        """Lấy dữ liệu hiển thị cho màn hình"""
        self.ensure_one()
        display_data = {
            'name': self.name,
            'location': self.location,
            'refresh_interval': self.refresh_interval,
            'show_estimated_time': self.show_estimated_time,
            'rooms': []
        }

        for room in self.room_ids:
            # Lấy token đang được phục vụ
            current_token = self.env['queue.token'].search([
                ('room_id', '=', room.id),
                ('state', '=', 'in_progress')
            ], limit=1)

            # Lấy danh sách token đang chờ
            waiting_tokens = self.env['queue.token'].search([
                ('room_id', '=', room.id),
                ('state', '=', 'waiting')
            ], order='position asc', limit=self.display_count)

            room_data = {
                'room_id': room.id,
                'room_name': room.name,
                'service_name': room.service_id.name,
                'current_token': current_token.name if current_token else False,
                'waiting_tokens': [
                    {
                        'name': t.name,
                        'position': t.position,
                        'wait_time': round(t.estimated_wait_time),
                        'emergency': t.emergency
                    } for t in waiting_tokens
                ]
            }

            display_data['rooms'].append(room_data)

        return display_data

    def action_view_public_display(self):
        """Mở màn hình hiển thị công khai trong tab mới"""
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return {
            'type': 'ir.actions.act_url',
            'url': f"{base_url}/queue/display/{self.id}",
            'target': 'new',
        }
