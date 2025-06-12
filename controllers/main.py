# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request

QUEUE_TOKEN = "queue.token"


class RouteGraphController(http.Controller):
    @http.route('/queue/route_graph', type='http', auth='user')
    def route_graph_view(self, **kwargs):
        """Render route graph visualization"""
        return request.render('hospital_queue_management.route_graph_page')


class QueueController(http.Controller):
    @http.route('/queue/dashboard/data', type='json', auth='user')
    def get_dashboard_data(self):
        """Lấy dữ liệu cho bảng điều khiển"""
        # Lấy tất cả phòng
        rooms = request.env['queue.room'].search([])
        room_data = []

        for room in rooms:
            # Token đang phục vụ
            current_token = request.env[QUEUE_TOKEN].search([
                ('room_id', '=', room.id),
                ('state', '=', 'in_progress')
            ], limit=1)

            # Tokens đang chờ
            waiting_tokens = request.env[QUEUE_TOKEN].search([
                ('room_id', '=', room.id),
                ('state', '=', 'waiting')
            ], order='position asc')

            # Thông tin phòng
            room_info = {
                'id': room.id,
                'name': room.name,
                'service': room.service_id.name,
                'state': room.state,
                'queue_length': room.queue_length,
                'estimated_wait_time': room.estimated_wait_time,
            }

            # Xử lý thông tin về token hiện tại
            if current_token:
                # Xử lý riêng cho trường priority
                current_token_priority = ''
                if current_token.priority_id:
                    current_token_priority = current_token.priority_id.name

                current_token_info = {
                    'id': current_token.id,
                    'name': current_token.name,
                    'patient': current_token.patient_id.name,
                    'priority': current_token_priority,
                    'emergency': current_token.emergency,
                    'start_time': current_token.start_time,
                }
                room_info['current_token'] = current_token_info
            else:
                room_info['current_token'] = False

            # Xử lý danh sách tokens đang chờ
            waiting_token_list = []
            for token in waiting_tokens:
                # Xử lý riêng cho trường priority của mỗi token
                token_priority = ''
                if token.priority_id:
                    token_priority = token.priority_id.name

                token_info = {
                    'id': token.id,
                    'name': token.name,
                    'patient': token.patient_id.name,
                    'position': token.position,
                    'priority': token_priority,
                    'emergency': token.emergency,
                    'wait_time': round(token.estimated_wait_time),
                }
                waiting_token_list.append(token_info)

            room_info['waiting_tokens'] = waiting_token_list

            room_data.append(room_info)

        # Thống kê tổng quan
        token_count = request.env[QUEUE_TOKEN].search_count([])
        waiting_count = request.env[QUEUE_TOKEN].search_count([('state', '=', 'waiting')])
        in_progress_count = request.env[QUEUE_TOKEN].search_count([('state', '=', 'in_progress')])
        completed_count = request.env[QUEUE_TOKEN].search_count([('state', '=', 'completed')])
        emergency_count = request.env[QUEUE_TOKEN].search_count(
            [('emergency', '=', True), ('state', 'in', ['waiting', 'in_progress'])])

        # Dữ liệu dịch vụ
        services = request.env['queue.service'].search([])
        service_data = []

        for service in services:
            tokens = request.env[QUEUE_TOKEN].search([('service_id', '=', service.id)])
            waiting = request.env[QUEUE_TOKEN].search_count([
                ('service_id', '=', service.id),
                ('state', '=', 'waiting')
            ])

            service_info = {
                'id': service.id,
                'name': service.name,
                'total': len(tokens),
                'waiting': waiting,
                'avg_time': service.average_duration,
            }

            service_data.append(service_info)

        # Dữ liệu trả về
        return {
            'rooms': room_data,
            'services': service_data,
            'statistics': {
                'total': token_count,
                'waiting': waiting_count,
                'in_progress': in_progress_count,
                'completed': completed_count,
                'emergency': emergency_count,
            },
            'timestamp': fields.Datetime.now(),
        }
