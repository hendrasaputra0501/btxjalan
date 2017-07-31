# -*- coding: utf-8 -*-
from . import ods


SUPPORTED = {}
SUPPORTED['ods'] = ods.SpreadSheetOds


def get_spreadsheet(spreadsheet_type, title):
    cls = SUPPORTED.get(spreadsheet_type)
    if cls is None:
        raise ValueError("Unsupported spreadsheet type: %r" % spreadsheet_type)

    return cls(title)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
