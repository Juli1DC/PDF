/* Copyright 2019 LevelPrime
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

odoo.define('eloapps_cash_flow_forecast', function (require) {
    'use strict';
    require('web.ActionManager').include({
        _handleAction: function (action, options) {
            if (action.type === 'ir.actions.act_window_close' &&  action.name === 'recurrentes close action') {
                return this._executeCloseWizardRefreshViewAction();
            }
            return this._super(action, options);
        },
        _executeCloseWizardRefreshViewAction: function () {
            this._closeDialog();
            var state = this._getControllerState(
                this.getCurrentController().jsID);
            return $.when(this.loadState(state));
        },
    });
});