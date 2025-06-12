from odoo import models, fields, api, _
from markupsafe import Markup

QUEUE_SERVICE_GROUP_ROUTE = "queue.service.group.route"
IR_ACTIONS_ACT_WINDOWN = "ir.actions.act_window"


class QueueServiceGroup(models.Model):
    _name = 'queue.service.group'
    _description = 'Nhóm Dịch Vụ Y Tế'
    _order = 'sequence'

    name = fields.Char(string='Tên Nhóm', required=True)
    code = fields.Char(string='Mã Nhóm', required=True)
    sequence = fields.Integer(string='Thứ Tự', default=10)
    service_ids = fields.Many2many('queue.service', string='Dịch Vụ Trong Nhóm')
    description = fields.Text(string='Mô Tả')
    is_required = fields.Boolean(string='Bắt Buộc', default=True,
                                 help="Nếu đánh dấu, tất cả dịch vụ trong nhóm phải hoàn thành. Nếu không, hoàn thành 1 dịch vụ có thể đủ để chuyển sang nhóm tiếp theo.")
    completion_policy = fields.Selection([
        ('all', 'Hoàn Thành Tất Cả'),
        ('any', 'Hoàn Thành Bất Kỳ'),
        ('custom', 'Tùy Chỉnh')
    ], string='Chính Sách Hoàn Thành', default='all')
    custom_rule = fields.Text(string='Quy Tắc Tùy Chỉnh',
                              help="Python expression để đánh giá điều kiện hoàn thành. Biến khả dụng: completed_services, total_services")
    active = fields.Boolean(string='Hoạt Động', default=True)
    color = fields.Integer(string='Màu', default=0)

    route_visualization_html = fields.Html(
        string="Route Visualization",
        compute="_compute_route_visualization",
        sanitize=False
    )

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Mã nhóm phải là duy nhất!')
    ]

    def action_view_services(self):
        """Xem danh sách dịch vụ trong nhóm"""
        self.ensure_one()
        return {
            'name': _('Dịch vụ trong %s') % self.name,
            'type': IR_ACTIONS_ACT_WINDOWN,
            'res_model': 'queue.service',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.service_ids.ids)],
        }

    def action_create_route(self):
        """Mở form tạo tuyến đường mới từ nhóm này"""
        self.ensure_one()
        return {
            'name': _('Tạo Tuyến Đường từ %s') % self.name,
            'type': IR_ACTIONS_ACT_WINDOWN,
            'res_model': QUEUE_SERVICE_GROUP_ROUTE,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_group_from_id': self.id,
            },
        }

    @api.depends('create_date')  # Dummy depends để trigger compute
    def _compute_route_visualization(self):
        """Generate HTML visualization for routes"""
        for record in self:
            # Lấy tất cả groups và routes
            groups = self.search([], order='sequence')
            routes = self.env[QUEUE_SERVICE_GROUP_ROUTE].search([])

            # Tạo HTML
            html = self._generate_route_html(groups, routes)
            record.route_visualization_html = html

    def _generate_route_html(self, groups, routes):
        """Generate SVG visualization"""
        svg_width = 900
        svg_height = 600
        node_radius = 60

        html = f"""
        <div style="width: 100%; overflow: auto; border: 1px solid #ddd; border-radius: 8px; background: white;">
            <svg width="{svg_width}" height="{svg_height}" style="display: block; margin: auto;">
                <defs>
                    <marker id="arrowhead" markerWidth="10" markerHeight="7"
                            refX="9" refY="3.5" orient="auto">
                        <polygon points="0 0, 10 3.5, 0 7" fill="#28a745"/>
                    </marker>
                </defs>
        """

        # Tính toán vị trí cho các nodes
        positions = {}
        cols = 3
        spacing_x = 250
        spacing_y = 200
        start_x = 150
        start_y = 100

        for idx, group in enumerate(groups):
            row = idx // cols
            col = idx % cols
            x = start_x + (col * spacing_x)
            y = start_y + (row * spacing_y)
            positions[group.id] = (x, y)

        # Vẽ các routes (đường nối)
        for route in routes:
            if (route.group_from_id.id in positions and route.group_to_id.id in positions):
                x1, y1 = positions[route.group_from_id.id]
                x2, y2 = positions[route.group_to_id.id]

                # Tính điểm cong cho đường
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2 - 50

                color = "#28a745" if not route.package_id else "#17a2b8"

                html += f"""
                <path d="M{x1},{y1} Q{mid_x},{mid_y} {x2},{y2}"
                      stroke="{color}" stroke-width="2" fill="none"
                      marker-end="url(#arrowhead)"/>
                """

                # Label cho route
                label = route.package_id.name if route.package_id else "Tất cả"
                html += f"""
                <text x="{mid_x}" y="{mid_y}" text-anchor="middle"
                      font-size="12" fill="#666">{label}</text>
                """

        # Vẽ các nodes (nhóm)
        for group in groups:
            if group.id in positions:
                x, y = positions[group.id]
                html += f"""
                <g class="route-node" data-group-id="{group.id}">
                    <circle cx="{x}" cy="{y}" r="{node_radius}"
                            fill="#4A6A8F" stroke="white" stroke-width="3"/>
                    <text x="{x}" y="{y}" text-anchor="middle"
                          fill="white" font-weight="bold" font-size="14">
                        {group.name}
                    </text>
                    <text x="{x}" y="{y + 20}" text-anchor="middle"
                          fill="white" font-size="12">
                        {group.code}
                    </text>
                </g>
                """

        html += """
            </svg>
        </div>

        <div class="mt-3 p-3 bg-light rounded">
            <h5>Hướng dẫn:</h5>
            <ul class="mb-0">
                <li><strong>Màu xanh lá:</strong> Tuyến đường áp dụng cho tất cả gói</li>
                <li><strong>Màu xanh dương:</strong> Tuyến đường cho gói cụ thể</li>
                <li>Click vào nút "Quản Lý Tuyến Đường" để thêm/sửa/xóa tuyến đường</li>
            </ul>
        </div>
        """

        return Markup(html)

    def action_view_route_report(self):
        """Open route analysis report"""
        return {
            'type': IR_ACTIONS_ACT_WINDOWN,
            'name': 'Phân Tích Tuyến Đường',
            'res_model': QUEUE_SERVICE_GROUP_ROUTE,
            'view_mode': 'graph,pivot',
            'target': 'current',
        }

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
                'to_id': route.group_to_id.id,
                'package_id': route.package_id.id if route.package_id else False,
                'package_name': route.package_id.name if route.package_id else _('Tất cả'),
            })

        return result
