# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

from osv import fields, osv


class port(osv.osv):
    _name = 'res.port'
    _description = 'port'
    _columns = {
        'name': fields.char('Port Name', size=64,
            help='The full name of the port.', translate=True),
        'code': fields.char('Port Code', size=5,
            help='The ISO port code in two chars.\n'
            'You can use this field for quick search.'),
        'country': fields.many2one('res.country','Country'),
    }
    

port()
