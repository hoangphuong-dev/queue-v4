/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted } from "@odoo/owl";

class QueueDisplayClient extends Component {
    setup() {
        super.setup();
        this.displayId = this.props?.action?.context?.display_id;

        onMounted(() => {
            this._openDisplay();
        });
    }

    async _openDisplay() {
        const displayIds = await this.env.services.rpc({
            model: "queue.display",
            method: "search",
            args: [[]],
            kwargs: {
                limit: 1,
            },
        });

        if (displayIds?.length) {
            const displayId = this.displayId || displayIds[0];
            const baseUrl = this.env.services.http.url('/');
            const url = baseUrl + "queue/display/" + displayId;
            window.open(url, "_blank");

            this.env.services.action.doAction({
                type: "ir.actions.act_window",
                res_model: "queue.display",
                views: [[false, "form"]],
                res_id: displayId,
            });
        } else {
            this.env.services.action.doAction({
                type: "ir.actions.act_window",
                res_model: "queue.display",
                views: [[false, "form"]],
                target: "current",
                context: {
                    create_display: true,
                },
            });
        }
    }
}

QueueDisplayClient.template = "hospital_queue_management.QueueDisplayClient";

registry.category("actions").add("queue_display_client", QueueDisplayClient);

export default QueueDisplayClient;