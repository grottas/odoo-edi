# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2016 Vertel AB (<http://vertel.se>).
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
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import re, urllib2, base64, unicodecsv as csv #pip install unicodecsv
import os
import openerp.tools as tools
from openerp.modules import get_module_path

import logging
_logger = logging.getLogger(__name__)


class res_partner(models.Model):
    _inherit='res.partner'

    gs1_gln = fields.Char(string="Global Location Number",help="GS1 Global Location Number (GLN)", select=True)
    customer_no = fields.Char(string="Customer No",help="The Customer No of the chain", select=True)

    @api.model
    def ica_update_store_registry(self):
        request = urllib2.Request("https://levnet.ica.se/Levnet/ButRegLev.nsf/wwwviwButiksfil/frmButiksfil/$FILE/butreg.xls")
        #sudo?
        #TODO: Error handling for parameters
        username = self.env['ir.config_parameter'].get_param('ica.levnet.username')
        password = self.env['ir.config_parameter'].get_param('ica.levnet.password')
        base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
        result = urllib2.urlopen(request)
        csv_data = csv.DictReader(utf_8_encoder(result), encoding='utf-8', dialect='excel', delimiter='\t')
        #"Företag", "Postadress", "Postnummer", "Ort", "Kundnummer",
        #"Lokaliseringskod, butik", "Lagerenhet", "Lokaliseringskod LE",
        #"Telefon", "Roll", "Lokaliseringskod godsadress", "Ändringsdatum"

        ica = self.env.ref('edi_gs1.ica_gruppen')
        if not ica:
            raise Warning("Couldn't find ICA central record (edi_gs1.ica_gruppen).")
        for row in csv_data:
            partner_values = {
                'name': excel_remove_clutter(row[u'Företag']),
                'gs1_gln': excel_remove_clutter(row[u'Lokaliseringskod, butik']),
                'street': excel_remove_clutter(row[u'Postadress']),
                'zip': excel_remove_clutter(row[u'Postnummer']),
                'city': excel_remove_clutter(row[u'Ort']),
                'phone': excel_remove_clutter(row[u'Telefon']),
                'ref': excel_remove_clutter(row[u'Kundnummer']),
                'parent_id': ica.id,
                'is_company': True,
                #~ 'foobar': excel_remove_clutter(csv_data[u'Lagerenhet']),
                #~ 'foobar': excel_remove_clutter(csv_data[u'Lokaliseringskod LE']),
                #~ 'foobar': excel_remove_clutter(csv_data[u'Roll']),
                #~ 'foobar': excel_remove_clutter(csv_data[u'Lokaliseringskod godsadress']),
                #~ 'foobar': excel_remove_clutter(csv_data[u'Ändringsdatum']),
            }
            partner = self.env['res.partner'].search([('gs1_gln', '=', partner_values['gs1_gln'])])
            #Remove redundant values
            for key in partner_values:
                if partner and getattr(partner, key) == partner_values[key]:
                    del(partner_values[key])
            _logger.warn("partner_values: %s" %partner_values)
            if partner:
                if partner_values:
                    partner.write(partner_values)
            else:
                partner.create(partner_values)

    @api.model
    def ica_update_logo(self):
        def _get_logo(img):
            return open(os.path.join(get_module_path('edi_gs1'), 'static', 'img', img), 'rb').read().encode('base64')

        for p in self.env['res.partner'].search([]):
            if (u'ICA') in p.name and (u'Nära') in p.name:
                p.image = _get_logo('ica_nara.jpg')
            elif (u'ICA') in p.name and (u'Supermarket') in p.name:
                p.image = _get_logo('ica_supermarket.jpg')
            elif (u'Apotek') in p.name and (u'Hjärtat') in p.name:
                p.image = _get_logo('apotek_hjartat.png')
            elif (u'ICA') in p.name and (u'Kvantum') in p.name:
                p.image = _get_logo('ica_kvantum.jpg')
            elif (u'Maxi') in p.name:
                p.image = _get_logo('ica_maxi.jpg')
            elif (u'ICA') in p.name:
                p.image = _get_logo('ica_nara.jpg')
            elif (u'Coop') in p.name and (u'Extra') in p.name:
                p.image = _get_logo('coop_extra.jpg')
            elif (u'Coop') in p.name and (u'Forum') in p.name:
                p.image = _get_logo('coop_forum.png')
            elif (u'Coop') in p.name and (u'Konsum') in p.name:
                p.image = _get_logo('coop_konsum.png')
            elif (u'Coop') in p.name and (u'Nära') in p.name:
                p.image = _get_logo('coop_nara.jpg')
            elif (u'Hemköp') in p.name:
                p.image = _get_logo(u'hemkop.jpg')
            elif (u'Willys') in p.name and (u'Hemma') in p.name:
                p.image = _get_logo('willys_hemma.png')
            elif (u'Willys') in p.name:
                p.image = _get_logo(u'willys.gif')
            elif (u'Tempo') in p.name:
                p.image = _get_logo('tempo.png')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
