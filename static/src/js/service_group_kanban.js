/** @odoo-module **/

import { registry } from "@web/core/registry";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { useState, onMounted } from "@odoo/owl";

export class ServiceGroupKanbanController extends KanbanController {
    setup() {
        super.setup();
        this.state = useState({
            isDragging: false,
            fromGroup: null,
            toGroup: null,
        });
    }

    /**
     * Xử lý sự kiện khi record được kéo vào nhóm khác
     * @override
     */
    // Cập nhật phương thức onRecordDropped trong ServiceGroupKanbanController

    async onRecordDropped(payload) {
        const {group: targetGroup, previousGroup } = payload;

        if (previousGroup && targetGroup && previousGroup.id !== targetGroup.id) {
            // Lấy dữ liệu cần thiết
            const fromGroupId = parseInt(previousGroup.id, 10);
            const toGroupId = parseInt(targetGroup.id, 10);

            // Mở wizard để người dùng tùy chỉnh tuyến đường
            this.actionService.doAction({
                type: 'ir.actions.act_window',
                res_model: 'queue.route.wizard',
                views: [[false, 'form']],
                target: 'new',
                context: {
                    from_group_id: fromGroupId,
                    to_group_id: toGroupId,
                },
            });
        } else {
            // Xử lý kéo thả thông thường (thay đổi sequence)
            return super.onRecordDropped(payload);
        }
    }

    /**
     * Hiển thị form để tạo tuyến đường mới
     */
    async onCreateRouteButtonClick(fromGroupId) {
        await this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'queue.service.group.route',
            views: [[false, 'form']],
            target: 'new',
            context: {
                default_group_from_id: fromGroupId,
            },
        });
    }
}

export class ServiceGroupKanbanRenderer extends KanbanRenderer {
    setup() {
        super.setup();

        onMounted(() => {
            this._setupArrows();
        });
    }

    /**
     * Thiết lập mũi tên giữa các nhóm để biểu thị tuyến đường
     * @private
     */
    _setupArrows() {
        const kanbanContainer = this.root.el;

        // Xóa các mũi tên cũ
        const existingArrows = kanbanContainer.querySelectorAll('.route-arrow');
        existingArrows.forEach(arrow => arrow.remove());

        // Lấy dữ liệu tuyến đường hiện tại
        this.env.services.rpc({
            model: 'queue.service.group.route',
            method: 'search_read',
            args: [
                [],
                ['group_from_id', 'group_to_id']
            ],
        }).then(routes => {
            // Tạo mũi tên cho mỗi tuyến đường
            routes.forEach(route => {
                const fromGroupElement = kanbanContainer.querySelector(`.o_kanban_group[data-id="${route.group_from_id[0]}"]`);
                const toGroupElement = kanbanContainer.querySelector(`.o_kanban_group[data-id="${route.group_to_id[0]}"]`);

                if (fromGroupElement && toGroupElement) {
                    const arrow = document.createElement('div');
                    arrow.className = 'route-arrow';
                    arrow.innerHTML = '<i class="fa fa-arrow-right"></i>';
                    fromGroupElement.appendChild(arrow);
                }
            });
        }).catch(error => {
            console.error("Lỗi khi lấy dữ liệu tuyến đường:", error);
        });
    }

    /**
     * Override để cập nhật lại mũi tên khi render lại view
     * @override
     */
    async renderView() {
        await super.renderView();
        this._setupArrows();
    }
}

export const serviceGroupKanbanView = {
    ...kanbanView,
    Controller: ServiceGroupKanbanController,
    Renderer: ServiceGroupKanbanRenderer,
};

registry.category("views").add("service_group_kanban", serviceGroupKanbanView);