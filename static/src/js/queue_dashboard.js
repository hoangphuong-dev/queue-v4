/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { _t } from "@web/core/l10n/translation";

class QueueDashboard extends Component {
    setup() {
        this.state = useState({
            dashboardData: {},
            isLoading: true,
        });

        this.refreshInterval = 30000; // 30 seconds
        this.refreshTimer = null;

        onWillStart(async () => {
            await this._fetchDashboardData();
        });

        onMounted(() => {
            this._startAutoRefresh();
        });

        onWillUnmount(() => {
            this._stopAutoRefresh();
        });
    }

    async _fetchDashboardData() {
        try {
            this.state.isLoading = true;
            const result = await this.env.services.rpc({
                route: "/queue/dashboard/data",
            });
            this.state.dashboardData = result;
        } catch (error) {
            this.env.services.notification.add(_t("Failed to load dashboard data"), {
                type: "danger",
            });
            console.error("Error loading dashboard data:", error);
        } finally {
            this.state.isLoading = false;
        }
    }

    _startAutoRefresh() {
        this._stopAutoRefresh();
        this.refreshTimer = browser.setTimeout(async () => {
            await this._refreshDashboard();
            this._startAutoRefresh();
        }, this.refreshInterval);
    }

    _stopAutoRefresh() {
        if (this.refreshTimer) {
            browser.clearTimeout(this.refreshTimer);
            this.refreshTimer = null;
        }
    }

    async _refreshDashboard() {
        await this._fetchDashboardData();
    }

    onRefreshClick() {
        this._refreshDashboard();
    }

    async onTokenActionClick(ev) {
        const action = ev.target.dataset.action;
        const tokenId = parseInt(ev.target.dataset.tokenId, 10);

        if (action && tokenId) {
            await this._callTokenAction(action, tokenId);
        }
    }

    async onRoomActionClick(ev) {
        const action = ev.target.dataset.action;
        const roomId = parseInt(ev.target.dataset.roomId, 10);

        if (action && roomId) {
            await this._callRoomAction(action, roomId);
        }
    }

    async _callTokenAction(action, tokenId) {
        try {
            await this.env.services.rpc({
                model: "queue.token",
                method: action,
                args: [[tokenId]],
            });
            await this._refreshDashboard();
        } catch (error) {
            this.env.services.notification.add(_t("Failed to perform action on token"), {
                type: "danger",
            });
            console.error("Error in token action:", error);
        }
    }

    async _callRoomAction(action, roomId) {
        try {
            await this.env.services.rpc({
                model: "queue.room",
                method: action,
                args: [[roomId]],
            });
            await this._refreshDashboard();
        } catch (error) {
            this.env.services.notification.add(_t("Failed to perform action on room"), {
                type: "danger",
            });
            console.error("Error in room action:", error);
        }
    }

    formatDateTime(dateTime) {
        if (!dateTime) return "";
        const date = new Date(dateTime);
        return date.toLocaleString();
    }

    formatTime(dateTime) {
        if (!dateTime) return "";
        const date = new Date(dateTime);
        return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }
}

QueueDashboard.template = "hospital_queue_management.QueueDashboard";
QueueDashboard.components = {};

registry.category("actions").add("queue_dashboard", QueueDashboard);

export default QueueDashboard;