from odoo import models, fields, api
from markupsafe import Markup


class QueueRouteDashboard(models.TransientModel):
    _name = 'queue.route.dashboard'
    _description = 'Dashboard Tuyến Đường'

    route_visualization_html = fields.Html(
        string="Route Visualization",
        compute="_compute_route_visualization",
        sanitize=False
    )

    @api.depends('create_date')
    def _compute_route_visualization(self):
        """Generate HTML visualization for routes"""
        for record in self:
            # Lấy tất cả groups và routes
            groups = self.env['queue.service.group'].search([], order='sequence')
            routes = self.env['queue.service.group.route'].search([])

            # Tạo HTML
            html = self._generate_route_html(groups, routes)
            record.route_visualization_html = html

    def _generate_route_html(self, groups, routes):
        """Generate SVG visualization"""
        if not groups:
            return Markup("""
                <div class="alert alert-info text-center">
                    <h4>Chưa có nhóm dịch vụ nào</h4>
                    <p>Vui lòng tạo nhóm dịch vụ trước khi xem sơ đồ tuyến đường</p>
                </div>
            """)

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
            'type': 'ir.actions.act_window',
            'name': 'Phân Tích Tuyến Đường',
            'res_model': 'queue.service.group.route',
            'view_mode': 'graph,pivot',
            'target': 'current',
        }
