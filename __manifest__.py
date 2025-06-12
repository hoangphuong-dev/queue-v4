# -*- coding: utf-8 -*-
{
    'name': "Quản Lý Hàng Đợi Khám Sức Khỏe",
    'summary': """
        Hệ thống quản lý hàng đợi khám sức khỏe thông minh dựa trên token
    """,
    # 'description': """
    #     Module này triển khai hệ thống quản lý hàng đợi thông minh cho cơ sở y tế, giúp:
    #     - Phân phối bệnh nhân hiệu quả giữa các phòng
    #     - Giảm thời gian chờ đợi
    #     - Ưu tiên các trường hợp khẩn cấp
    #     - Hỗ trợ định tuyến tự động giữa các dịch vụ
    #     - Cung cấp công cụ giám sát trực quan cho nhân viên
    # """,
    'author': "Mate Technology JSC",
    'website': "https://www.yourcompany.com",
    'category': 'Healthcare',
    'version': '18.0.1.0.0',
    'depends': ['base', 'mail', 'sms', 'web'],
    'data': [
        # Thứ tự này rất quan trọng
        # 1. Đầu tiên là cấu trúc bảo mật và dữ liệu cơ bản

        'security/queue_security.xml',
        'data/queue_data.xml',
        'data/queue_demo.xml',
        'data/queue_service_group_demo.xml',
        'data/room_reservation_demo.xml',
        'data/queue_room_distance_demo.xml',
        'data/coordination_actions.xml',

        # 2. Các views và biểu mẫu (để model được tạo ra)
        'views/queue_views.xml',
        'views/partner_views.xml',
        'views/queue_display_views.xml',
        'views/dashboard_views.xml',
        'views/queue_service_group_views.xml',
        'views/queue_views_extended.xml',
        'views/health_check_views.xml',
        'views/room_reservation_views.xml',
        'views/queue_room_distance_views.xml',
        'views/queue_service_group_route_views.xml',
        'views/route_dashboard_views.xml',
        'views/route_management_views.xml',
        'views/menu_views.xml',
        'views/queue_room_selection_wizard_views.xml',
        'views/queue_token_coordination_views.xml',

        # 3. Báo cáo
        'report/queue_report_templates.xml',
        'report/queue_report.xml',

        # 4. Templates email và SMS
        'data/mail_template_data.xml',
        'data/sms_template_data.xml',
        'data/patient_demo_data.xml',
        'data/token_demo_data.xml',

        # 5. Cuối cùng là file quyền truy cập sau khi tất cả model đã được tạo ra
        'security/ir.model.access.csv',
        'security/ir.rule.csv',
    ],
    'qweb': [
        # 'static/src/xml/queue_dashboard_templates.xml',
        'static/src/xml/queue_display_templates.xml',
        'static/src/xml/queue_kanban_templates.xml',
        'static/src/xml/queue_token_form_buttons.xml',
        'static/src/xml/queue_client_action_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hospital_queue_management/static/src/js/view_tree_with_token.js',
            'hospital_queue_management/static/src/js/queue_token_form.js',
            'hospital_queue_management/static/src/js/queue_client_action.js',
            'hospital_queue_management/static/src/js/queue_dashboard.js',
            'hospital_queue_management/static/src/scss/queue_dashboard.scss',
            'hospital_queue_management/static/src/scss/patient_kanban.scss',
            'hospital_queue_management/static/src/scss/patient_detail.scss',

            'hospital_queue_management/static/src/xml/tree_button_templates.xml',
            'hospital_queue_management/static/src/xml/queue_token_form_buttons.xml',
            'hospital_queue_management/static/src/xml/queue_client_action_templates.xml',
            'hospital_queue_management/static/src/xml/queue_dashboard_templates.xml',

            'hospital_queue_management/static/src/js/route_dashboard.js',
            'hospital_queue_management/static/src/scss/route_dashboard.scss',
            'hospital_queue_management/static/src/xml/route_dashboard.xml',
            'hospital_queue_management/static/src/scss/route_visualization.scss',

            'hospital_queue_management/static/src/css/patient_details.css',
            'hospital_queue_management/static/src/scss/coordination.scss',
            'hospital_queue_management/static/src/scss/patient_coordination.scss',

            'hospital_queue_management/static/src/js/queue_coordination_kanban.js',
        ],
    },
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'images': [
        'static/description/banner.png',
    ],
}
