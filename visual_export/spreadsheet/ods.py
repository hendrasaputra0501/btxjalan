# -*- coding: utf-8 -*-

from . import base
from odf import opendocument
from odf.table import Table, TableRow, TableCell


class SpreadSheetOdsRow(object):

    def __init__(self, doc):
        self.number = doc.nextline
        doc.nextline += 1
        self.nextcell = 0
        self.row = TableRow()
        doc.table.addElement(self.row)

    def AddCell(self, attributes=None, rowspan=1, colspan=1):
        tc = TableCell(attributes=attributes)
        tc.number = self.nextcell
        self.nextcell += colspan
        tc.setAttribute('numberrowsspanned', str(rowspan))
        tc.setAttribute('numbercolumnsrepeated', str(colspan))
        tc.setAttribute('numbercolumnsspanned', str(colspan))
        self.row.addElement(tc)
        return tc

    def AddStringCell(self, value, **kwargs):
        attributes = {
            'valuetype': 'string',
            'stringvalue': unicode(value),
        }
        return self.AddCell(attributes=attributes, **kwargs)

    def AddFormulaCell(self, value, **kwargs):
        attributes = {
            'valuetype': 'string',
            'formula': value,
        }
        return self.AddCell(attributes=attributes, **kwargs)

    def AddDoubleCell(self, value, **kwargs):
        attributes = {
            'valuetype': 'float',
            'value': value,
        }
        return self.AddCell(attributes=attributes, **kwargs)

    def AddDecimalCell(self, value, **kwargs):
        attributes = {
            'valuetype': 'currency',
            'value': str(value),
        }
        return self.AddCell(attributes=attributes, **kwargs)

    def AddDateCell(self, value, **kwargs):
        attributes = {
            'valuetype': 'date',
            'datevalue': value,
        }
        return self.AddCell(attributes=attributes, **kwargs)

    def AddDateTimeCell(self, value, date_only=False, tz=None, **kwargs):

        if not date_only:
            if tz is not None:
                raise NotImplementedError("No support for timezones yet.")
            # This is UTC time
            value = value.split('.')[0].replace(' ', 'T')

        attributes = {
            'valuetype': 'date',
            'datevalue': value,
        }
        return self.AddCell(attributes=attributes, **kwargs)

    def AddBooleanCell(self, value, **kwargs):
        attributes = {
            'valuetype': 'boolean',
            'booleanvalue': value,
        }
        return self.AddCell(attributes=attributes, **kwargs)


class SpreadSheetOds(base.SpreadSheetBase):

    def __init__(self, title):
        super(SpreadSheetOds, self).__init__(title)
        self.nextline = 1
        self.document = opendocument.OpenDocumentSpreadsheet()
        self.table = Table(name=title)
        self.document.spreadsheet.addElement(self.table)

    def AddRow(self, style=None):
        return SpreadSheetOdsRow(self)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
