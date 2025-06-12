/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class RouteDashboard extends Component {
    static template = "hospital_queue_management.RouteDashboard";
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            groups: [],
            routes: [],
            selectedGroup: null,
            isLoading: true,
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        try {
            this.state.isLoading = true;

            // Sử dụng orm service thay vì rpc
            const [groups, routes] = await Promise.all([
                this.orm.searchRead(
                    "queue.service.group",
                    [],
                    ["name", "code", "sequence"],
                    { order: "sequence" }
                ),
                this.orm.searchRead(
                    "queue.service.group.route",
                    [],
                    ["group_from_id", "group_to_id", "package_id", "condition"]
                ),
            ]);

            this.state.groups = groups;
            this.state.routes = routes;
        } catch (error) {
            this.notification.add(_t("Lỗi khi tải dữ liệu"), {
                type: "danger"
            });
            console.error("Error loading data:", error);
        } finally {
            this.state.isLoading = false;
        }
    }

    onGroupClick(groupId) {
        this.state.selectedGroup = groupId;
    }

    async onCreateRoute() {
        await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "queue.service.group.route",
            views: [[false, "form"]],
            target: "new",
            context: {},
        });
    }

    async onViewStatistics() {
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: _t("Thống Kê Tuyến Đường"),
            res_model: "queue.service.group.route",
            views: [[false, "pivot"], [false, "graph"]],
            target: "current",
        });
    }

    getGroupPosition(groupId, index) {
        const cols = 3;
        const row = Math.floor(index / cols);
        const col = index % cols;
        const spacing = 250;
        const startX = 150;
        const startY = 150;

        return {
            x: startX + (col * spacing),
            y: startY + (row * spacing),
        };
    }

    getRouteConnection(route) {
        const fromIndex = this.state.groups.findIndex(
            g => g.id === route.group_from_id[0]
        );
        const toIndex = this.state.groups.findIndex(
            g => g.id === route.group_to_id[0]
        );

        if (fromIndex === -1 || toIndex === -1) {
            return null;
        }

        const from = this.getGroupPosition(
            route.group_from_id[0],
            fromIndex
        );
        const to = this.getGroupPosition(
            route.group_to_id[0],
            toIndex
        );

        return { from, to };
    }
}

registry.category("actions").add("route_dashboard", RouteDashboard);