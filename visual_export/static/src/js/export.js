openerp.visual_export = function (instance) {

    var _t = instance.web._t;
    var QWeb = instance.web.qweb;

    instance.web.ListView.include({
        load_list: function () {
            var self = this;
            var add_button = false;
            if (!this.$buttons) {
                add_button = true;
            }
            this._super.apply(this, arguments);
            if(add_button) {
                var dashboard_actions = window.$('.oe_dashboard .oe_action');
                _(dashboard_actions).each(function(action){
                    var act = $(action);
                    if (act.find('.oe_list.oe_view')[0] === self.el){
                        var text = act.find('.oe_header_txt');
                        var $button = $(QWeb.render("VisualExport", {'widget':self}));
                        $button.insertAfter(text);
                        $button.on('click', function() {
                            self.export_by_visual_export();
                        });
                    }
                });
                this.$buttons.on('click', '.oe_list_button_export', function() {
                    self.export_by_visual_export();
                });
            }
        },
        get_export_fields_and_headers: function(){
            var fields = [];
            var headers = [];
            _(this.visible_columns).each(function(c){
                if (c.name) fields.push(c.name);
                headers.push(c.string);
            });
            return [fields, headers];
        },
        get_export_other_filter: function(){
            return {};
        },
        export_by_visual_export: function() {
            var self = this;
            fields_and_headers = this.get_export_fields_and_headers();
            $.blockUI();
            var export_domain = [];
            if(this.groups.datagroup.domain.__domains){
                domains = this.groups.datagroup.domain.__domains;
                for (index = 0; index < domains.length; ++index) {
                    export_domain = export_domain.concat(domains[index]);
                }
            }else{
                export_domain = this.groups.datagroup.domain;
            }
            self.session.get_file({
                url: '/web/export/spreadsheet_view',
                data: {data: JSON.stringify({
                    model: this.model,
                    fields: fields_and_headers[0],
                    headers: fields_and_headers[1],
                    domain: export_domain,
                    groupby: this.groups.datagroup.group_by,
                    grouped: this.grouped,
                    view_type: this.view_type,
                    other_filter: this.get_export_other_filter(),
                    title: this.options.action.name,
                    context: this.groups.datagroup.context,
                    view_mode: 'list'
                })},
                complete: $.unblockUI
            });
        },
    });
    instance.web.TreeView.include({
        load_tree: function () {
            var self = this;
            var add_button = false;
            if (!this.$buttons) {
                this.$buttons = $(QWeb.render("ListView.buttons", {'widget':self}));
                if (this.options.$buttons) {
                    this.$buttons.appendTo(this.options.$buttons);
                } else {
                    this.$el.find('.oe_list_buttons').replaceWith(this.$buttons);  
                }
                add_button = true;
            }
            this._super.apply(this, arguments);
            if(add_button) {
                this.$buttons.on('click', '.oe_list_button_export', function() {
                    fields_and_headers = self.get_export_fields_and_headers();
                    $.blockUI();
                    self.session.get_file({
                        url: '/web/export/spreadsheet_view',
                        data: {data: JSON.stringify({
                            model: self.model,
                            fields: fields_and_headers[0],
                            headers: fields_and_headers[1],
                            view_type: self.view_type,
                            other_filter: self.get_export_other_filter(),
                            title: self.options.action.name,
                            view_mode: 'tree',
                            child_field: self.get_export_child_field(),
                            domain: self.dataset.domain,
                            context: self.dataset.context
                        })},
                        complete: $.unblockUI
                    });
                });
            }
        },
        get_export_fields_and_headers: function(){
            var fields = [];
            var headers = [];
            var self = this;
            _(this.fields_view.arch.children).each(function(c){
                if (!c.attrs.modifiers.tree_invisible){
                    fields.push(c.attrs.name);
                    headers.push(c.attrs.string || self.fields[c.attrs.name].string);
                }
            });
            return [fields, headers];
        },
        get_export_other_filter: function(){
            var $select = this.$el.find('select') 
            var $option = $select.find(':selected');
            res = {id: $option.val()};
            return res;
        },
        get_export_child_field: function(){
            return this.children_field;
        },
    });
};
