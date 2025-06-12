# -*- coding: utf-8 -*-
from odoo import models, api
import json
QUEUE_TOKEN = "queue.token"
REPORT_QUEUE_STATISTICS = "report.hospital_queue_management.report_queue_statistics"


class QueueStatisticsReport(models.AbstractModel):
    _name = REPORT_QUEUE_STATISTICS
    _description = 'Báo Cáo Thống Kê Hàng Đợi'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Lấy dữ liệu cho báo cáo thống kê"""
        if not data:
            data = {}

        # Lấy dữ liệu từ wizard
        wizard_id = data.get('wizard_id')
        wizard = self.env['queue.statistics.wizard'].browse(wizard_id)

        # Lấy dữ liệu báo cáo
        report_data = wizard.get_report_data(data)

        return {
            'doc_ids': docids,
            'doc_model': QUEUE_TOKEN,
            'docs': self.env[QUEUE_TOKEN].browse(docids),
            'data': data,
            'report_data': report_data,
        }

    @api.model
    def _get_html_report_values(self, docids, data=None):
        """Lấy dữ liệu cho báo cáo HTML"""
        if not data:
            data = {}

        # Lấy dữ liệu báo cáo
        report_data = self.env['queue.statistics.wizard'].get_report_data(data)

        # Chuyển đổi dữ liệu sang JSON để sử dụng trong biểu đồ
        if 'grouped_data' in report_data:
            chart_data = []
            for item in report_data['grouped_data']:
                chart_data.append({
                    'name': item['name'],
                    'total': item['total'],
                    'completed': item.get('completed', 0),
                    'cancelled': item.get('cancelled', 0),
                })
            report_data['chart_data_json'] = json.dumps(chart_data)

        # Thêm dữ liệu biểu đồ cho thời gian chờ
        if data.get('report_type') == 'waiting_time' and 'waiting_times' in report_data:
            wait_time_data = [
                {'name': item['name'], 'value': item['avg_wait_time']}
                for item in report_data['waiting_times']
            ]
            report_data['wait_time_chart_json'] = json.dumps(wait_time_data)

        # Thêm dữ liệu biểu đồ cho thời gian phục vụ
        if data.get('report_type') == 'service_time' and 'service_times' in report_data:
            service_time_data = [
                {'name': item['name'], 'value': item['avg_service_time']}
                for item in report_data['service_times']
            ]
            report_data['service_time_chart_json'] = json.dumps(service_time_data)

        return {
            'doc_ids': docids,
            'doc_model': QUEUE_TOKEN,
            'docs': self.env[QUEUE_TOKEN].browse(docids),
            'data': data,
            'report_data': report_data,
        }


# Định nghĩa các báo cáo cụ thể
class QueueSummaryReport(models.AbstractModel):
    _name = 'report.hospital_queue_management.report_queue_summary'
    _inherit = REPORT_QUEUE_STATISTICS


class QueueDetailedReport(models.AbstractModel):
    _name = 'report.hospital_queue_management.report_queue_detailed'
    _inherit = REPORT_QUEUE_STATISTICS


class QueueWaitingTimeReport(models.AbstractModel):
    _name = 'report.hospital_queue_management.report_queue_waiting_time'
    _inherit = REPORT_QUEUE_STATISTICS


class QueueServiceTimeReport(models.AbstractModel):
    _name = 'report.hospital_queue_management.report_queue_service_time'
    _inherit = REPORT_QUEUE_STATISTICS
