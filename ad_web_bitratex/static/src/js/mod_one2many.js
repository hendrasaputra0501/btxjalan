openerp.ad_web_bitratex = function(instance){
    var _t = instance.web._t,
    _lt = instance.web._lt;
    var QWeb = instance.web.qweb;
    var module = instance.web.form // loading the namespace of the 'sample' module
    var mody = instance.web

    module.AbstractFormPopup.include({
        
        setup_form_view: function() {
            var self = this;
            if (this.row_id) {
                this.dataset.ids = [this.row_id];
                this.dataset.index = 0;
            } else {
                this.dataset.index = null;
            }
            var options = _.clone(self.options.form_view_options) || {};
            if (this.row_id !== null) {
                options.initial_mode = this.options.readonly ? "view" : "edit";
            }
            _.extend(options, {
                $buttons: this.$buttonpane,
            });
            this.view_form = new instance.web.FormView(this, this.dataset, this.options.view_id || false, options);
            if (this.options.alternative_form_view) {
                this.view_form.set_embedded_view(this.options.alternative_form_view);
            }
            this.view_form.appendTo(this.$el.find(".oe_popup_form"));
            this.view_form.on("form_view_loaded", self, function() {
                var multi_select = self.row_id === null && ! self.options.disable_multiple_selection;
                self.$buttonpane.html(QWeb.render("AbstractFormPopup.buttons", {
                    multi_select: multi_select,
                    readonly: self.row_id !== null && self.options.readonly,
                }));
                var $snbutton = self.$buttonpane.find(".oe_abstractformpopup-form-save-new");
                $snbutton.click(function() {
                    console.log(this)
                    $.when(self.view_form.save()).done(function() {
                        self.view_form.reload_mutex.exec(function() {
                            self.view_form.on_button_new();
                        });
                    });
                });
                var $scbutton = self.$buttonpane.find(".oe_abstractformpopup-form-save-copy");
                $scbutton.click(function() {
                    // newrec = new self.view_form.datarecord.constructor();
                    // for (var attr in self.view_form.datarecord) {
                    //         if (self.view_form.datarecord.hasOwnProperty(attr)) {
                    //             newrec[attr] = self.view_form.datarecord[attr];
                    //         }
                    //     }

                    $.when(self.view_form.save()).done(function() {
                        newrec = self.view_form.datarecord
                        //console.log("Pertama");
                        //console.log(newrec);
                        self.view_form.reload_mutex.exec(function() {
                            newrec.id=self.view_form.datarecord.id
                            self.view_form.on_button_new_copy(newrec)
                            // self.view_form.load_record(newrec);
                            // console.log("Ketiga");
                            // console.log(self.view_form.datarecord);
                        });
                    });
                });
                var $sbutton = self.$buttonpane.find(".oe_abstractformpopup-form-save");
                $sbutton.click(function() {
                    //console.log(this.context)
                    $.when(self.view_form.save()).done(function() {
                        self.view_form.reload_mutex.exec(function() {
                            self.check_exit();
                        });
                    });
                });
                var $cbutton = self.$buttonpane.find(".oe_abstractformpopup-form-close");
                $cbutton.click(function() {
                    self.view_form.trigger('on_button_cancel');
                    self.check_exit();
                });
                self.view_form.do_show();
            });
        },
    });


    mody.FormView.include({
        on_button_new_copy: function(newrec) {
            var self = this;
            this.to_edit_mode();
            return $.when(this.has_been_loaded).then(function() {
                if (self.can_be_discarded()) {
                    console.log("New Copy");
                    console.log(newrec);
                    return self.load_defaults_copy(newrec);
                }
            });
        },

        load_defaults_copy: function (newrec) {
            var self = this;
            var keys = _.keys(this.fields_view.fields);
            if (keys.length) {
                // console.log("LOAD DEFAULT COPY");
                // console.log(this.dataset.default_get(keys));
                return this.dataset.default_get(keys).then(function(r) {
                    
                    for (var attr in newrec) {
                            if (newrec.hasOwnProperty(attr)) {
                                if (attr!="id")
                                    {
                                    r[attr] = newrec[attr];
                                    }
                            }
                        }
                    console.log("Defaults Copy");
                    console.log(r);
                    self.trigger('load_record', r);
                });
            }
            return self.trigger('load_record', {});
        },
    });
};

/*
instance.web.form.AbstractFormPopup = instance.web.Widget.extend({
    template: "AbstractFormPopup.render",
    /**
     *  options:
     *  -readonly: only applicable when not in creation mode, default to false
     * - alternative_form_view
     * - view_id
     * - write_function
     * - read_function
     * - create_function
     * - parent_view
     * - child_name
     * - form_view_options
     *
    init_popup: function(model, row_id, domain, context, options) {
        this.row_id = row_id;
        this.model = model;
        this.domain = domain || [];
        this.context = context || {};
        this.options = options;
        _.defaults(this.options, {
        });
    },
    init_dataset: function() {
        var self = this;
        this.created_elements = [];
        this.dataset = new instance.web.ProxyDataSet(this, this.model, this.context);
        this.dataset.read_function = this.options.read_function;
        this.dataset.create_function = function(data, options, sup) {
            var fct = self.options.create_function || sup;
            return fct.call(this, data, options).done(function(r) {
                self.trigger('create_completed saved', r);
                self.created_elements.push(r);
            });
        };
        this.dataset.write_function = function(id, data, options, sup) {
            var fct = self.options.write_function || sup;
            return fct.call(this, id, data, options).done(function(r) {
                self.trigger('write_completed saved', r);
            });
        };
        this.dataset.parent_view = this.options.parent_view;
        this.dataset.child_name = this.options.child_name;
    },
    display_popup: function() {
        var self = this;
        this.renderElement();
        var dialog = new instance.web.Dialog(this, {
            min_width: '800px',
            dialogClass: 'oe_act_window',
            close: function() {
                self.check_exit(true);
            },
            title: this.options.title || "",
        }, this.$el).open();
        this.$buttonpane = dialog.$buttons;
        this.start();
    },
    setup_form_view: function() {
        var self = this;
        if (this.row_id) {
            this.dataset.ids = [this.row_id];
            this.dataset.index = 0;
        } else {
            this.dataset.index = null;
        }
        var options = _.clone(self.options.form_view_options) || {};
        if (this.row_id !== null) {
            options.initial_mode = this.options.readonly ? "view" : "edit";
        }
        _.extend(options, {
            $buttons: this.$buttonpane,
        });
        this.view_form = new instance.web.FormView(this, this.dataset, this.options.view_id || false, options);
        if (this.options.alternative_form_view) {
            this.view_form.set_embedded_view(this.options.alternative_form_view);
        }
        this.view_form.appendTo(this.$el.find(".oe_popup_form"));
        this.view_form.on("form_view_loaded", self, function() {
            var multi_select = self.row_id === null && ! self.options.disable_multiple_selection;
            self.$buttonpane.html(QWeb.render("AbstractFormPopup.buttons", {
                multi_select: multi_select,
                readonly: self.row_id !== null && self.options.readonly,
            }));
            var $snbutton = self.$buttonpane.find(".oe_abstractformpopup-form-save-new");
            $snbutton.click(function() {
                $.when(self.view_form.save()).done(function() {
                    self.view_form.reload_mutex.exec(function() {
                        self.view_form.on_button_new();
                    });
                });
            });
            var $scbutton = self.$buttonpane.find(".oe_abstractformpopup-form-save-copy");
            $scbutton.click(function() {
                alert("Copy");
                $.when(self.view_form.save()).done(function() {
                    self.view_form.reload_mutex.exec(function() {
                        
                    });
                });
            });
            var $sbutton = self.$buttonpane.find(".oe_abstractformpopup-form-save");
            $sbutton.click(function() {
                $.when(self.view_form.save()).done(function() {
                    self.view_form.reload_mutex.exec(function() {
                        self.check_exit();
                    });
                });
            });
            var $cbutton = self.$buttonpane.find(".oe_abstractformpopup-form-close");
            $cbutton.click(function() {
                self.view_form.trigger('on_button_cancel');
                self.check_exit();
            });
            self.view_form.do_show();
        });
    },
    select_elements: function(element_ids) {
        this.trigger("elements_selected", element_ids);
    },
    check_exit: function(no_destroy) {
        if (this.created_elements.length > 0) {
            this.select_elements(this.created_elements);
            this.created_elements = [];
        }
        this.trigger('closed');
        this.destroy();
    },
    destroy: function () {
        this.trigger('closed');
        if (this.$el.is(":data(dialog)")) {
            this.$el.dialog('close');
        }
        this._super();
    },
});
*/