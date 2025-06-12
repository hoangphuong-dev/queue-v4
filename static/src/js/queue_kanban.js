odoo.define('hospital_queue_management.queue_kanban', function (require) {
    "use strict";

    const KanbanController = require('web.KanbanController');
    const KanbanView = require('web.KanbanView');
    const viewRegistry = require('web.view_registry');

    const QueueKanbanController = KanbanController.extend({
        buttons_template: 'QueueKanbanView.buttons',
        events: _.extend({}, KanbanController.prototype.events, {
            'click .o_queue_refresh': '_onRefreshClick',
            'click .o_queue_balance': '_onBalanceClick',
        }),

        /**
         * @override
         */
        init: function (parent, model, renderer, params) {
            this._super(parent, model, renderer, ...arguments);
            this.hasButtons = true;
        },

        _onRefreshClick: function (ev) {
            ev.preventDefault();
            this.reload();
        },

        _onBalanceClick: function (ev) {
            ev.preventDefault();
            const self = this;
            this._rpc({
                model: 'queue.token',
                method: '_run_load_balancing',
                args: [],
            }).then(function () {
                self.reload();
            });
        },
    });

    const QueueKanbanView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: QueueKanbanController,
        }),
    });

    viewRegistry.add('queue_token_kanban', QueueKanbanView);

    return {
        QueueKanbanController,
        QueueKanbanView,
    };
});