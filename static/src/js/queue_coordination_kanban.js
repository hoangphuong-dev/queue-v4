/** @odoo-module **/

import { KanbanController } from '@web/views/kanban/kanban_controller';
import { registry } from '@web/core/registry';
import { kanbanView } from '@web/views/kanban/kanban_view';
import { useService } from "@web/core/utils/hooks";

class QueueCoordinationKanbanController extends KanbanController {
    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.notification = useService("notification");
    }

    /**
     * Override to handle reordering
     */
    async onReorder(dataRecordId, dataGroupId, { oldIndex, newIndex }) {
        const record = this.model.root.records.find(r => r.resId === dataRecordId);

        if (!record) return;

        // Calculate new position based on surrounding records
        const group = this.model.root.groups.find(g => g.resId === dataGroupId);
        const records = group.records;

        let newPosition;
        if (newIndex === 0) {
            // Moved to top
            newPosition = 1;
        } else if (newIndex >= records.length - 1) {
            // Moved to bottom
            newPosition = records.length;
        } else {
            // Moved to middle - calculate based on neighbors
            const prevRecord = records[newIndex - 1];
            const nextRecord = records[newIndex + 1];

            if (prevRecord && nextRecord) {
                newPosition = Math.floor((prevRecord.data.position + nextRecord.data.position) / 2);
            } else {
                newPosition = newIndex + 1;
            }
        }

        const oldPosition = record.data.position;

        // Call server method to update position
        try {
            await this.rpc("/web/dataset/call_kw/queue.token/reorder_position", {
                model: "queue.token",
                method: "reorder_position",
                args: [record.resId, newPosition, oldPosition],
                kwargs: {},
            });

            // Reload to refresh positions
            await this.model.load();

            this.notification.add(
                `Token ${record.data.name} đã được di chuyển từ vị trí ${oldPosition} đến vị trí ${newPosition}`,
                { type: "success" }
            );

        } catch (error) {
            this.notification.add(
                "Không thể di chuyển token: " + error.message,
                { type: "danger" }
            );
            // Reload to reset view
            await this.model.load();
        }
    }
}

// Register custom kanban view
registry.category("views").add("queue_coordination_kanban", {
    ...kanbanView,
    Controller: QueueCoordinationKanbanController,
});