# -*- coding: utf-8 -*-
import openerp.addons.web.http as openerpweb
import simplejson


class ExportController(openerpweb.Controller):

    _cp_path = '/web/export/spreadsheet_view'

    @openerpweb.httprequest
    def index(self, request, data, token):
        view = request.session.model('ir.ui.view')
        kwargs = simplejson.loads(data)
        spreadsheet = view.get_export(**kwargs)
        try:
            return request.make_response(
                spreadsheet,
                headers=[
                    ('Content-Disposition', 'attachment; filename="%s.ods"'
                     % kwargs['title']),
                    ('Content-Type', 'application/vnd.oasis.opendocument.spreadsheet')
                ], cookies={'fileToken': int(token)})
        except:
            return request.make_response(
                spreadsheet,
                headers=[
                    ('Content-Disposition', 'attachment; filename="%s.ods"'
                     % kwargs['title']),
                    ('Content-Type', 'application/vnd.oasis.opendocument.spreadsheet')
                ], cookies={'fileToken': token})
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
