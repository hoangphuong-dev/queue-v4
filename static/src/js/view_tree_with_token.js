/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";
import { _t } from "@web/core/l10n/translation";

export class ViewTreeWithTokenController extends ListController {
    setup() {
        super.setup();
    }

    /**
     * @override
     */
    async onClickViewButton(kwargs) {
        await super.onClickViewButton(kwargs);
        if (kwargs.name === "o_list_button_generate_token") {
            this._onGenerateToken();
        }
    }

    /**
     * Handler khi nhấn nút tạo token
     * @private
     */
    async _onGenerateToken() {
        const selectedRecords = this.getSelectedRecords();

        if (selectedRecords.length === 0) {
            this.env.services.notification.add(_t("Vui lòng chọn ít nhất một bệnh nhân."), {
                type: "warning",
                title: _t("Cảnh Báo"),
            });
            return;
        }

        const selectedIds = selectedRecords.map((record) => record.resId);

        await this.actionService.doAction({
            name: _t("Tạo Token Hàng Loạt"),
            type: "ir.actions.act_window",
            res_model: "queue.generate.token.wizard",
            views: [[false, "form"]],
            target: "new",
            context: {
                default_patient_ids: selectedIds,
            },
        });
    }
}

export const viewTreeWithToken = {
    ...listView,
    Controller: ViewTreeWithTokenController,
    buttonTemplate: "hospital_queue_management.ListViewButtons",
};

registry.category("views").add("view_tree_with_token", viewTreeWithToken);