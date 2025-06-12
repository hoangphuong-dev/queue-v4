from odoo import models, fields, api, _


class QueueRouteWizard(models.TransientModel):
    _name = 'queue.route.wizard'
    _description = 'Wizard Tùy chỉnh Tuyến Đường'

    group_from_id = fields.Many2one('queue.service.group', string='Từ Nhóm', required=True, readonly=True)
    group_to_id = fields.Many2one('queue.service.group', string='Đến Nhóm', required=True, readonly=True)
    package_id = fields.Many2one('queue.package', string='Gói Dịch Vụ Cụ Thể')
    condition = fields.Text(string='Điều Kiện Chuyển')
    sequence = fields.Integer(string='Độ Ưu Tiên', default=10)
    notes = fields.Text(string='Ghi chú')

    @api.model
    def default_get(self, fields_list):
        """Lấy giá trị mặc định từ context"""
        res = super(QueueRouteWizard, self).default_get(fields_list)

        # Lấy dữ liệu từ context khi được gọi từ JavaScript
        if self.env.context.get('from_group_id') and self.env.context.get('to_group_id'):
            res.update({
                'group_from_id': self.env.context.get('from_group_id'),
                'group_to_id': self.env.context.get('to_group_id'),
            })

        return res

    def action_create_route(self):
        """Tạo tuyến đường với thông tin chi tiết"""
        self.ensure_one()

        # Kiểm tra xem tuyến đường đã tồn tại chưa
        existing_route = self.env['queue.service.group.route'].search([
            ('group_from_id', '=', self.group_from_id.id),
            ('group_to_id', '=', self.group_to_id.id)
        ], limit=1)

        if existing_route:
            # Cập nhật tuyến đường hiện có
            existing_route.write({
                'package_id': self.package_id.id,
                'condition': self.condition,
                'sequence': self.sequence,
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Thành công'),
                    'message': _('Tuyến đường đã được cập nhật'),
                    'sticky': False,
                    'type': 'success',
                }
            }
        else:
            # Tạo tuyến đường mới
            route_vals = {
                'group_from_id': self.group_from_id.id,
                'group_to_id': self.group_to_id.id,
                'package_id': self.package_id.id,
                'condition': self.condition,
                'sequence': self.sequence,
            }

            self.env['queue.service.group.route'].create(route_vals)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Thành công'),
                    'message': _('Tuyến đường mới đã được tạo'),
                    'sticky': False,
                    'type': 'success',
                }
            }
