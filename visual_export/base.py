# -*- coding: utf-8 -*-

from openerp.osv import osv
from . import spreadsheet


def object_descriptor(obj, cr, uid, fields_get, fields, context):
    f = fields[0]
    if f not in fields_get.keys():
        return (None, None, None)
    field_type = fields_get[f]['type']
    model = fields_get[f].get('relation')
    field_descriptor = fields_get[f]['string']
    if len(fields) == 1 or (len(fields) == 2 and fields[1] == 'id'):
        pass
    else:
        fget = obj.pool.get(model).fields_get(cr, uid, context=context)
        field_type, model, desc = object_descriptor(
            obj, cr, uid, fget, fields[1:], context)
        field_descriptor += ' / ' + desc
    return (field_type, model, field_descriptor)


class IrUiView(osv.Model):
    _inherit = 'ir.ui.view'

    def get_export_title(self, cr, uid, doc, obj, **kwargs):
        if hasattr(obj, 'get_export_title'):
            return obj.get_export_title(cr, uid, doc, **kwargs)
        row = doc.AddRow()
        number_column = len(kwargs.get('fields'))
        if kwargs.get('grouped'):
            number_column += 1

        row.AddStringCell(kwargs.get('title'), colspan=number_column)
        row = doc.AddRow()
        row = doc.AddRow()

    def get_export_criteria_group_by(self, cr, uid, obj, fields_get, groupby):
        if hasattr(obj, 'get_export_criteria_group_by'):
            return obj.get_export_criteria_group_by(
                cr, uid, fields_get, groupby)
        return [fields_get[f]['string'] for f in groupby]

    def get_export_criteria_domain(self, cr, uid, obj, fields_get, domain, context):
        if hasattr(obj, 'get_export_criteria_domain'):
            return obj.get_export_criteria_domain(
                cr, uid, fields_get, domain, context)
        filters = []
        while domain:
            x = domain.pop()
            if x == '&':
                filters.append('et')
            elif x == '|':
                filters.append('ou')
            else:
                field, op, val = x
                ftype, fmodel, fdesc = object_descriptor(
                    self, cr, uid, fields_get, field.split('.'), context)
                if ftype == 'many2one':
                    if val:
                        if not isinstance(val, (list, tuple)):
                            val = [val]
                        for v in self.pool.get(fmodel).name_get(cr, uid, val,
                                                                context=context):
                            filters.append('%s %s %s' % (fdesc or field, op, v[1]))
                    else:
                        filters.append('%s %s %s' % (fdesc, op, val))

                else:
                    filters.append('%s %s %s' % (fdesc or field, op, val))
        return filters

    def get_export_criteria(self, cr, uid, doc, obj, fields_get, **kwargs):
        if hasattr(obj, 'get_export_criteria'):
            return obj.get_export_criteria(cr, uid, doc, **kwargs)

        number_column = len(kwargs.get('fields'))
        row = doc.AddRow()
        colspan = 1
        if kwargs.get('grouped'):
            number_column += 1
            colspan = number_column / 2
            row.AddStringCell(u'Filter by ...', colspan=colspan)
            row.AddStringCell(u'Group by ...', colspan=colspan)
        else:
            colspan = number_column
            row.AddStringCell(u'Filter by ...', colspan=colspan)

        domain = [] + kwargs.get('domain', [])
        groupby = [] + kwargs.get('groupby', [])
        context = kwargs.get('context', {}).copy()

        filters = self.get_export_criteria_domain(
            cr, uid, obj, fields_get, domain, context)
        groupby = self.get_export_criteria_group_by(
            cr, uid, obj, fields_get, groupby)
        while filters or groupby:
            row = doc.AddRow()
            if filters and groupby:
                row.AddStringCell(filters.pop(), colspan=colspan)
                row.AddStringCell(groupby.pop(), colspan=colspan)
            elif filters:
                row.AddStringCell(filters.pop(), colspan=colspan)
            else:
                row.AddStringCell('', colspan=colspan)
                row.AddStringCell(groupby.pop(), colspan=colspan)

    def get_export_header(self, cr, uid, doc, obj, **kwargs):
        if hasattr(obj, 'get_export_header'):
            return obj.get_export_header(cr, uid, doc, **kwargs)
        row = doc.AddRow()
        for header in kwargs.get('headers'):
            row.AddStringCell(header)

    def get_export_row_add_field(self, cr, uid, obj, row, value, fields_get,
                                 field, context=None):
        if value is None:
            return row.AddStringCell('')

        field_descr = fields_get.get(field)
        if field_descr is None:
            if isinstance(value, (int, long, float)):
                return row.AddDoubleCell(value)
            else:
                return row.AddStringCell(unicode(value))

        field_type = field_descr['type']
        if field_type == 'char':
            return row.AddStringCell(value)
        elif field_type == 'many2one':
            if value:
                return row.AddStringCell(value[1])
            else:
                return row.AddStringCell('')
        elif field_type in ('integer', 'float'):
            return row.AddDoubleCell(value)
        elif field_type == 'decimal':
            return row.AddDecimalCell(value)
        elif field_type == 'boolean':
            return row.AddBooleanCell(value)
        elif field_type == 'selection':
            selection = dict(fields_get[field]['selection']).get(value, '')
            return row.AddStringCell(unicode(selection))
        elif field_type == 'date':
            return row.AddDateTimeCell(value, date_only=True)
        elif field_type == 'datetime':
            # TODO pass user's timezone
            return row.AddDateTimeCell(value)
        else:
            return row.AddStringCell('Not Implemented Yet: %r' % field_type)

    def get_export_row_read(self, cr, uid, doc, obj, domain, fields,
                            fields_get, grouped=False, context=None):
        obj_ids = obj.search(cr, uid, domain, context=context)  # TODO sort
        rows = []
        for read in obj.read(cr, uid, obj_ids, fields, context=context):
            row = doc.AddRow()
            rows.append(row)
            if grouped:
                row.AddStringCell('')
            for f in fields:
                self.get_export_row_add_field(
                    cr, uid, obj, row, read[f], fields_get, f, context=context)

        return rows

    def get_export_row_group(self, cr, uid, doc, obj, domain, groupby, fields,
                             fields_get, level=0, context=None):
        fields2read = list(set(fields).union(set(groupby)))
        rows = []
        n=0
        for g in obj.read_group(cr, uid, domain, fields2read, groupby,
                                context=context):
            n+=1
            #print n,"g==============",g
            row = doc.AddRow()
            rows.append(row)
            if isinstance(g[groupby[0]], (list, tuple)):
                gstring = g[groupby[0]][1]
            else:
                gstring = g[groupby[0]]
            #print "gstringgstringxxxxxxxxxxxxxx",gstring
            try:
                row.AddStringCell('%s%s (%d)' % (
                    ' - ' * level, gstring, g[groupby[0] + '_count']))
            except:
                row.AddStringCell('%s%s ' % (
                    ' - ' * level, gstring))
            new_groupby = g['__context'].get('group_by')
            new_domain = g['__domain']
            if new_groupby:
                subrows = self.get_export_row_group(
                    cr, uid, doc, obj, new_domain, new_groupby, fields,
                    fields_get, level=level + 1, context=context)
            else:
                subrows = self.get_export_row_read(
                    cr, uid, doc, obj, new_domain, fields, fields_get,
                    grouped=True, context=context)

            for f in fields:
                if f != groupby[0] and fields_get[f]['type'] in ('integer',
                                                                 'float',
                                                                 'decimal'):
                    use_read_group = getattr(
                        obj._columns[f], 'visual_export_use_read_group', False)
                    if use_read_group:
                        self.get_export_row_add_field(cr, uid, obj, row,
                                                      g[f], fields_get, f,
                                                      context=context)
                    else:
                        group_operator = fields_get[f].get(
                            'group_operator', 'sum').upper()
                        # It is uggly but by default if it is False or None
                        # the group by put a SUM

                        if group_operator == 'AVG':
                            group_operator = 'AVERAGE'

                        cnumber = row.nextcell
                        minsubcell = '%s%d' % (chr(ord('A') + cnumber),
                                               min([r.number for r in subrows]))
                        maxsubcell = '%s%d' % (chr(ord('A') + cnumber),
                                               max([r.number for r in subrows]))
                        val = '=%s(%s:%s)' % (group_operator, minsubcell,
                                              maxsubcell)
                        row.AddFormulaCell(val)
                else:
                    row.AddStringCell('')

        return rows

    def get_export_rows(self, cr, uid, doc, obj, fields_get, **kwargs):
        if hasattr(obj, 'get_export_rows'):
            return obj.get_export_rows(cr, uid, doc, obj, **kwargs)
        domain = [] + kwargs.get('domain', [])
        groupby = [] + kwargs.get('groupby', [])
        context = kwargs.get('context', {}).copy()
        fields = [] + kwargs.get('fields')
        if kwargs.get('grouped'):
            self.get_export_row_group(cr, uid, doc, obj, domain, groupby,
                                      fields, fields_get, context=context)
        else:
            self.get_export_row_read(
                cr, uid, doc, obj, domain, fields, fields_get, context=context)
        doc.AddRow()
        doc.AddRow()

    def get_export_tree_rows(self, cr, uid, doc, obj, fields_get, **kwargs):
        if hasattr(obj, 'get_export_tree_rows'):
            return obj.get_export_tree_rows(cr, uid, doc, obj, **kwargs)
        fields = [] + kwargs.get('fields')
        child_field = kwargs['child_field']
        toread = fields + [child_field]

        def getdata(ids, level):
            for r in obj.read(cr, uid, ids, toread, context=context):
                row = doc.AddRow()
                for c in fields:
                    if c == fields[0] and r[child_field]:
                        val = " - " * level + '> ' + unicode(r[c])
                        row.AddStringCell(val)
                    elif c == fields[0]:
                        val = " - " * level + unicode(r[c])
                        row.AddStringCell(val)
                    else:
                        self.get_export_row_add_field(
                            cr, uid, obj, row, r[c], fields_get, c,
                            context=context)

                if r[child_field]:
                    getdata(r[child_field], level + 1)

        domain = [('parent_id', '=', int(kwargs['other_filter']['id']))]
        context = kwargs.get('context', {}).copy()
        obj_ids = obj.search(cr, uid, domain, context=context)
        getdata(obj_ids, 0)
        doc.AddRow()
        doc.AddRow()
        return domain

    def get_export(self, cr, uid, **kwargs):
        doc = spreadsheet.get_spreadsheet('ods', kwargs.get('title'))
        obj = self.pool.get(kwargs.get('model'))
        if hasattr(obj, 'get_export_domain_context'):
            kwargs['domain'], kwargs['context'] = obj.get_export_domain_context(
                cr, uid, **kwargs)
        self.get_export_title(cr, uid, doc, obj, **kwargs)
        self.get_export_header(cr, uid, doc, obj, **kwargs)
        fields_get = obj.fields_get(cr, uid, context=kwargs.get('context'))
        if kwargs.get('view_mode') == 'list':
            self.get_export_rows(cr, uid, doc, obj, fields_get, **kwargs)
        elif kwargs.get('view_mode') == 'tree':
            kwargs['domain'] = self.get_export_tree_rows(
                cr, uid, doc, obj, fields_get, **kwargs)
        self.get_export_criteria(cr, uid, doc, obj, fields_get, **kwargs)
        return doc.tofile()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
