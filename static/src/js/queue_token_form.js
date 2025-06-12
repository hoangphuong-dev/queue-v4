/** @odoo-module **/

import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";
import { _t } from "@web/core/l10n/translation";

export class QueueTokenFormController extends FormController {
    setup() {
        super.setup();
    }

    /**
     * @override
     */
    async onClickViewButton(kwargs) {
        await super.onClickViewButton(kwargs);
        if (kwargs.name === "o_queue_print_token") {
            this._onPrintToken();
        } else if (kwargs.name === "o_queue_emergency_override") {
            this._onEmergencyOverride();
        }
    }

    async _onPrintToken() {
        await this.model.root.save();
        await this.actionService.doAction({
            type: "ir.actions.report",
            report_name: "hospital_queue_management.report_queue_token",
            report_type: "qweb-pdf",
            context: { active_id: this.model.root.resId },
        });
    }

    async _onEmergencyOverride() {
        await this.model.root.save();
        await this.rpc({
            model: "queue.token",
            method: "action_emergency_override",
            args: [[this.model.root.resId]],
        });
        await this.model.root.load();
        this.env.services.notification.add(_t("Token đã được đánh dấu là khẩn cấp và được ưu tiên cao nhất."), {
            type: "success",
            title: _t("Thành Công"),
        });
    }

    /**
     * @override
     */
    updateButtons() {
        super.updateButtons();
        if (this.$buttons) {
            const state = this.model.root.data;
            const emergency = state.emergency;
            const current_state = state.state;

            const emergencyBtn = this.$buttons.find(".o_queue_emergency_override");
            if (emergencyBtn.length) {
                emergencyBtn.toggleClass("d-none", emergency || current_state === "completed" || current_state === "cancelled");
            }
        }
    }
}

export const queueTokenFormView = {
    ...formView,
    Controller: QueueTokenFormController,
    buttonTemplate: "hospital_queue_management.FormViewButtons",
};

registry.category("views").add("queue_token_form", queueTokenFormView);