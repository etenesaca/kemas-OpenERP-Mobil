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
from lxml import etree
from tools.translate import _
from mx import DateTime
from datetime import *
from datetime import timedelta
from datetime import datetime
import time
import datetime 
from kemas import kemas_extras
import addons
import unicodedata
import random
import logging
import calendar
import pooler
import threading
from mx import DateTime
import base64
import openerp
import tools
import math
from dateutil.parser import  *
from openerp import SUPERUSER_ID
_logger = logging.getLogger(__name__)

class kemas_config(osv.osv): 
    _columns = {
        'mobile_background': fields.binary('Fondo', help='Es la imagen que estla como fndo en el menu de Colaboradores.'),
        'mobile_background_text_color':fields.char('Color de la letra', size=64, help='Color del texto del Menu.'),
        }
    
    _inherit = 'kemas.config' 
    
class kemas_history_points(osv.osv): 
    def get_points_to_mobilapp(self, cr, uid, ids, context={}):
        sql = """
            SELECT H.points, H.type, H.date FROM kemas_history_points as H
            WHERE H.id in %s
            """ % (kemas_extras.convert_to_tuple_str(ids))
        cr.execute(sql)
        print ids
        return cr.fetchall()

    _inherit = 'kemas.history.points' 
    
class kemas_attendance(osv.osv): 
    def get_attendances_to_mobilapp(self, cr, uid, ids, context={}):
        sql = """
            SELECT A.id, S.name, A.type, A.date FROM kemas_attendance as A
            JOIN kemas_event as E ON (E.id = A.event_id)
            JOIN kemas_service as S ON (S.id = E.service_id)
            WHERE A.id in %s
            ORDER BY A.date DESC
            """ % (kemas_extras.convert_to_tuple_str(ids))
        cr.execute(sql)
        print ids
        return cr.fetchall()

    _inherit = 'kemas.attendance' 

class kemas_collaborator(osv.osv):
    def get_collaborator(self, cr, uid, collaborator_id, context={}):
        def build_image(image):
            result = ''
            if not image is None and type(image).__name__ == 'buffer':
                try:
                    result = unicode(image)
                except: None
            return result
                
        sql = """
            SELECT 
                Cl.id, Cl.personal_id, CL.code,CL.name,Cl.nick_name,Cl.birth,Cl.marital_status,Cl.address,Cl.photo_Large as image_medium,
                Cl.mobile,Cl.telef1,Cl.telef2,Cl.email,Cl.im_account,
                Cl.join_date,CL.points,LV.name as level, CL.team_id, Cl.genre
            FROM kemas_collaborator as CL
            JOIN res_users as U on (Cl.user_id = U.id)
            JOIN res_partner as P on (U.partner_id = P.id)
            JOIN kemas_level as LV on(CL.level_id = LV.id)
            WHERE Cl.id = %d
            """ % collaborator_id
        cr.execute(sql)
        collaborators = cr.dictfetchall()
        if collaborators:
            collaborator = collaborators[0]
            # Obtener el listado de Areas de Colaboracion
            sql = """
                SELECT name,logo_small as logo FROM kemas_area as A
                JOIN kemas_collaborator_area_rel as REL ON (REL.area_id = A.id)
                WHERE REL.collaborator_id = %s
                """ % str(collaborator['id'])
            cr.execute(sql)
            collaborator['areas'] = cr.dictfetchall()
            for area in collaborator['areas']:
                area['logo'] = build_image(area['logo'])
            
            # Obtener el equipo
            if collaborator['team_id']:
                sql = """
                    SELECT name,logo_medium as logo FROM kemas_team
                    WHERE id = %s
                    """ % str(collaborator['team_id'])
                cr.execute(sql)
                collaborator['team'] = cr.dictfetchall()[0]
                collaborator['team']['logo'] = build_image(collaborator['team']['logo'])
            else:
                collaborator['team'] = ''
            collaborator.pop('team_id')
            
            # Poner en español el estado civil
            lgenre = {'Male': 'o', 'Female': 'a'}
            if collaborator['marital_status'] == 'single':
                collaborator['marital_status'] = 'Soleter' + lgenre[collaborator['genre']]
            else:
                collaborator['marital_status'] = 'Casad' + lgenre[collaborator['genre']]
                    
            # Poner la foto en el formato correcto
            collaborator['image_medium'] = build_image(collaborator['image_medium'])
        
            # Calcular la edad
            collaborator['age'] = kemas_extras.calcular_edad(collaborator['birth'])
            collaborator['birth'] = kemas_extras.convert_date_format_short_str(collaborator['birth'])
            
            # Calcular edad en el ministerio
            collaborator['age_in_ministry'] = kemas_extras.calcular_edad(collaborator['join_date'], 4)
            collaborator['join_date'] = kemas_extras.convert_date_format_short_str(collaborator['join_date'])
            
            
            for field in collaborator:
                if collaborator[field] is None:
                    collaborator[field] = ' -- '
            return collaborator
        else:
            return False
        
    def get_info_for_navigation(self, cr, uid, collaborator_id, context={}):
        def build_image(image):
            result = ''
            if not image is None and type(image).__name__ == 'buffer':
                try:
                    result = unicode(image)
                except: None
            return result
        
        sql = """
            SELECT P.name,CL.photo_medium as image, CL.team_id
            FROM kemas_collaborator as CL
            JOIN res_users as U on (Cl.user_id = U.id)
            JOIN res_partner as P on (U.partner_id = P.id)
            WHERE Cl.id = %d
            """ % collaborator_id
        cr.execute(sql)
        collaborators = cr.dictfetchall()
        if collaborators:
            result = {}
            collaborator = collaborators[0]
            collaborator['image'] = build_image(collaborator['image'])
            # Obtener el equipo
            if collaborator['team_id']:
                sql = """
                    SELECT name FROM kemas_team
                    WHERE id = %s
                    """ % str(collaborator['team_id'])
                cr.execute(sql)
                collaborator['team'] = cr.dictfetchall()[0]['name']
            else:
                collaborator['team'] = ''
            collaborator.pop('team_id')
            result.update(collaborator)
            
            sql = """
                select mobile_background,mobile_background_text_color from kemas_config
                """
            cr.execute(sql)
            config = cr.dictfetchall()[0]
            config['mobile_background'] = build_image(config['mobile_background'])
            result.update(config)
            return result
        else:
            return False
        
    _inherit = 'kemas.collaborator' 
    
# vim:expandtab:smartind:tabstop=4:softtabstop=4:shiftwidth=4:
