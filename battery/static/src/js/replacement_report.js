odoo.define('battery.replacement_reort',function (require) {
    'use strict';
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var session = require('web.session');
    var QWeb = core.qweb;
    // var table = new Tabulator();

    // concise
    var replacement_report = AbstractAction.extend({
        template: 'DynamicStk',

        init: function (view, code) {
            this._super(view, code);
            this.wizard_id = code.context.wizard_id
        },
        start: function () {
            var self = this;
            self.load_data();
        },
        load_data: function () {
            var self = this;
            if (!self.wizard_id) {
                var paramValue = new URLSearchParams(window.location.href).get('active_id');
                self.wizard_id = [parseInt(paramValue)]
            }
            self._rpc({
                model: 'hop.replacement.report.wiz',
                method: 'report_data',
                args: [self.wizard_id],
            }).then(function (datas) {
                self.$('.py-data-container-orig').html(QWeb.render('DataSectionall', {
                    header: datas[0]
                }));
                var columns = datas[3];
                var table = myFunction(columns,datas[1],datas[2]) 
            });
        },

    });
    core.action_registry.add('replace.battery', replacement_report);
});
