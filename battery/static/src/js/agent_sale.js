odoo.define("dynamic_report.agent_sale_rpt",function (require) {
    'use strict';
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var session = require('web.session');
    var QWeb = core.qweb;
    // var table = new Tabulator();

    var agentsaleconc = AbstractAction.extend({
        template: 'DynamicStk',

        init: function (view, code) {
            this._super(view, code);
            this.wizard_id = code.context.wizard_id
            this.from_Date = code.context.from_date
            this.to_Date = code.context.to_date
            this.session = session;
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
                model: 'agent.sale.rpt.wizard',
                method: 'get_report_agent_sale',
                args: [self.wizard_id],
            }).then(function (datas) {
                console.log(datas)
                self.$('.py-data-container-orig').html(QWeb.render('DataSectionall', {
                    header: datas[0]
                }));
                var columns = datas[3];
                columns.forEach(function (column) {
                    if (column.field === 'bill_no') {
                        column.cellClick = function (e, cell) {
                            var id = cell.getRow().getData()["id"];
                            self.do_action({
                                name: "Agent Sale",
                                views: [[false, 'form']],
                                view_type: 'form',
                                res_model: 'hop.agent.sale',
                                type: 'ir.actions.act_window',
                                target: 'new',
                                res_id: id,
                                flags:{mode:'readonly'},
                                context: {'create': false}
                            });
                        };
                    }
                });
                var table = myFunction(columns,datas[1],datas[2],"sale_bill_rpt")
            //    });
                
            });
        },

    });
    
    core.action_registry.add('agent.sale.rpt', agentsaleconc);core.action_registry;
});
