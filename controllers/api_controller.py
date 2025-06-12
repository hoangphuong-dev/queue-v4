# -*- coding: utf-8 -*-
from odoo import http, fields, _
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)
QUEUE_TOKEN = "queue.token"


class QueueApiController(http.Controller):
    @http.route('/api/queue/test', type='http', auth='public', methods=['GET'], csrf=False)
    def test_api(self, **kwargs):
        return json.dumps({"status": "ok"})

    @http.route('/api/queue/token/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_token(self, **post):
        """
        Tạo token mới cho bệnh nhân và dịch vụ cụ thể

        Tham số JSON cần gửi:
        - patient_id: ID của bệnh nhân (bắt buộc)
        - service_id: ID của dịch vụ (bắt buộc)
        - service_type: Loại dịch vụ ('regular', 'health_check', 'insurance', 'emergency')
        - emergency: Boolean chỉ ra nếu là trường hợp khẩn cấp
        - notes: Ghi chú bổ sung
        - health_check_batch_id: ID của đợt khám sức khỏe (tùy chọn)
        - external_reference: Mã tham chiếu từ hệ thống bên ngoài
        """
        try:
            # Xác thực dữ liệu bắt buộc
            data = request.jsonrequest

            if not data.get('patient_id') or not data.get('service_id'):
                return {
                    'success': False,
                    'message': _('Yêu cầu có patient_id và service_id')
                }

            # Kiểm tra bệnh nhân tồn tại
            patient = request.env['res.partner'].sudo().browse(data.get('patient_id'))
            if not patient.exists() or not patient.is_patient:
                return {
                    'success': False,
                    'message': _('Không tìm thấy bệnh nhân hoặc bệnh nhân không hợp lệ')
                }

            # Kiểm tra dịch vụ tồn tại
            service = request.env['queue.service'].sudo().browse(data.get('service_id'))
            if not service.exists():
                return {
                    'success': False,
                    'message': _('Không tìm thấy dịch vụ')
                }

            # Chuẩn bị dữ liệu tạo token
            vals = {
                'patient_id': data.get('patient_id'),
                'service_id': data.get('service_id'),
                'service_type': data.get('service_type', 'regular'),
                'emergency': data.get('emergency', False),
                'notes': data.get('notes', ''),
                'health_check_batch_id': data.get('health_check_batch_id', False),
                'state': 'draft',  # Trạng thái ban đầu
            }

            # Thêm mã tham chiếu ngoài nếu có
            if data.get('external_reference'):
                vals['notes'] = f"{vals['notes']}\nMã tham chiếu: {data.get('external_reference')}"

            # Tạo token mới
            token = request.env[QUEUE_TOKEN].sudo().create(vals)

            # Chuyển sang trạng thái chờ để kích hoạt xử lý tự động
            if not token.is_parallel:
                token.sudo().write({'state': 'waiting'})

            return {
                'success': True,
                'token': {
                    'id': token.id,
                    'name': token.name,
                    'room_id': token.room_id.id,
                    'room_name': token.room_id.name,
                    'position': token.position,
                    'estimated_wait_time': token.estimated_wait_time,
                    'state': token.state,
                },
                'message': _('Tạo token thành công')
            }

        except Exception as e:
            _logger.error("Lỗi khi tạo token qua API: %s", str(e))
            return {'success': False, 'message': str(e)}

    @http.route('/api/queue/token/status/<int:token_id>', type='http', auth='user', methods=['GET'], csrf=False)
    def get_token_status(self, token_id, **kwargs):
        """
        Lấy trạng thái của một token cụ thể
        """
        try:
            token = request.env[QUEUE_TOKEN].sudo().browse(token_id)
            if not token.exists():
                return json.dumps({'success': False, 'message': 'Token không tồn tại'})

            result = {
                'success': True,
                'token': {
                    'id': token.id,
                    'name': token.name,
                    'patient_id': token.patient_id.id,
                    'patient_name': token.patient_id.name,
                    'service_id': token.service_id.id,
                    'service_name': token.service_id.name,
                    'room_id': token.room_id.id,
                    'room_name': token.room_id.name,
                    'position': token.position,
                    'state': token.state,
                    'estimated_wait_time': token.estimated_wait_time,
                    'start_time': token.start_time and fields.Datetime.to_string(token.start_time) or False,
                    'emergency': token.emergency,
                }
            }

            return json.dumps(result)

        except Exception as e:
            _logger.error("Lỗi khi lấy trạng thái token: %s", str(e))
            return json.dumps({'success': False, 'message': str(e)})

    @http.route('/api/queue/token/list', type='http', auth='user', methods=['GET'], csrf=False)
    def get_tokens_list(self, **kwargs):
        """
        Lấy danh sách token theo các bộ lọc
        """
        try:
            domain = []
            limit = min(int(kwargs.get('limit', 50)), 100)  # Giới hạn tối đa 100 bản ghi

            # Xây dựng bộ lọc
            if kwargs.get('service_id'):
                domain.append(('service_id', '=', int(kwargs.get('service_id'))))

            if kwargs.get('room_id'):
                domain.append(('room_id', '=', int(kwargs.get('room_id'))))

            if kwargs.get('state'):
                domain.append(('state', '=', kwargs.get('state')))

            if kwargs.get('service_type'):
                domain.append(('service_type', '=', kwargs.get('service_type')))

            # Tìm kiếm token
            tokens = request.env[QUEUE_TOKEN].sudo().search(domain, limit=limit, order='create_date desc')

            result = {
                'success': True,
                'count': len(tokens),
                'tokens': [{
                    'id': token.id,
                    'name': token.name,
                    'patient_name': token.patient_id.name,
                    'service_name': token.service_id.name,
                    'room_name': token.room_id.name,
                    'position': token.position,
                    'state': token.state,
                    'estimated_wait_time': token.estimated_wait_time,
                    'emergency': token.emergency,
                } for token in tokens]
            }

            return json.dumps(result)

        except Exception as e:
            _logger.error("Lỗi khi lấy danh sách token: %s", str(e))
            return json.dumps({'success': False, 'message': str(e)})

    @http.route('/api/queue/token/cancel/<int:token_id>', type='json', auth='user', methods=['POST'], csrf=False)
    def cancel_token(self, token_id, **post):
        """
        Hủy một token
        """
        try:
            token = request.env[QUEUE_TOKEN].sudo().browse(token_id)
            if not token.exists():
                return {'success': False, 'message': 'Token không tồn tại'}

            if token.state in ['completed', 'cancelled']:
                return {'success': False, 'message': f'Token đã ở trạng thái {token.state}, không thể hủy'}

            # Lấy lý do hủy nếu có
            data = request.jsonrequest
            reason = data.get('reason', 'Hủy qua API')

            # Hủy token
            token.sudo().write({
                'state': 'cancelled',
                'notes': f"{token.notes or ''}\nLý do hủy: {reason}"
            })

            # Cập nhật lại vị trí trong hàng đợi
            token._add_to_queue_and_sort()

            return {
                'success': True,
                'message': 'Token đã được hủy thành công'
            }

        except Exception as e:
            _logger.error("Lỗi khi hủy token: %s", str(e))
            return {'success': False, 'message': str(e)}
