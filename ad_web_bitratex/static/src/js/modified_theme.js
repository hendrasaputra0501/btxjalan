// openerp.ad_web_bitratex = function(instance){
//     var QWeb = instance.web.qweb;
//     var _t = instance.web._t,
//     _lt = instance.web._lt;

//     instance.web.form.CompletionFieldMixin.include({
//         get_search_result: function(search_val) {
//             var self = this;

//             var dataset = new instance.web.DataSet(this, this.field.relation, self.build_context());
//             var blacklist = this.get_search_blacklist();
//             this.last_query = search_val;
            
//             var current_context= self.build_context();
//             //var dump =current_context["__contexts"][0].replace(/[\{\}]/g, '').split(",");
//             //console.debug(current_context["__contexts"][0]);
//             var current_context_inside = JSON.stringify(current_context["__contexts"][0].replace(/[\{\}\"]/g,"").replace(/False/g,"false").replace(/True/g,"true"));
//             //console.debug("=========current_context_inside"+current_context_inside+"  "+typeof(current_context_inside));
//             var s1=current_context_inside.split(",");
//             var modified_context = new Object();
//             for (x=0;x<s1.length;x++)
//                 {
//                 var s2=s1[x].split(":");
//                 modified_context[s2[0].replace(/[\{\}\"\']/g,"")]=s2[1].replace(/[\{\}\"\']/g,"");
//                 }
//             //var current_context_inside = JSON.parse(eval(current_context_inside));
//             return this.orderer.add(dataset.name_search(
//                     search_val, new instance.web.CompoundDomain(self.build_domain(), [["id", "not in", blacklist]]),
//                     'ilike', this.limit + 1, self.build_context())).then(function(data) {
//                 self.last_search = data;
//                 // possible selections for the m2o
//                 var values = _.map(data, function(x) {
//                     x[1] = x[1].split("\n")[0];
//                     return {
//                         label: _.str.escapeHTML(x[1]),
//                         value: x[1],
//                         name: x[1],
//                         id: x[0],
//                     };
//                 });

//                 // search more... if more results that max
//                 if (values.length > self.limit) {
//                     values = values.slice(0, self.limit);
//                     values.push({
//                         label: _t("Search More..."),
//                         action: function() {
//                             dataset.name_search(search_val, self.build_domain(), 'ilike', 160).done(function(data) {
//                                 self._search_create_popup("search", data);
//                             });
//                         },
//                         classname: 'oe_m2o_dropdown_option'
//                     });
//                 }
//                 // quick create
//                 //if (!("create" in current_context["__eval_context"]["__contexts"][1]) || current_context["__eval_context"]["__contexts"][1]["create"]==true)
//                 // console.debug(modified_context['create'],typeof(modified_context['create']));
//                 if (!(modified_context.hasOwnProperty('create')) || modified_context['create']==="true")
//                     {
//                         var raw_result = _(data.result).map(function(x) {return x[1];});
//                         if (search_val.length > 0 && !_.include(raw_result, search_val)) {
//                             values.push({
//                                 label: _.str.sprintf(_t('Create "<strong>%s</strong>"'),
//                                     $('<span />').text(search_val).html()),
//                                 action: function() {
//                                     self._quick_create(search_val);
//                                 },
//                                 classname: 'oe_m2o_dropdown_option'
//                             });
//                         }
//                         values.push({
//                             label: _t("Create and Edit..."),
//                             action: function() {
//                                 self._search_create_popup("form", undefined, self._create_context(search_val));
//                             },
//                             classname: 'oe_m2o_dropdown_option'
//                         });
//                     }
//                 return values;
//             });
//         },
//     });

// }