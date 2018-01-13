# -*- coding:utf-8 -*-

##############################################################################
# MobilEPR - A small self-hosted ERP that works with your smartphone.
# Copyright (C) 2017  Eligio Becerra
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################

from flask import abort, jsonify, make_response, request

from models import db_session, engine
from models.Product import Product as Product
from models.PriceHistory import PriceHistory as PriceHistory
from models.views import DepletedItems
from models.MasterList import MasterList as MasterList
from models.views import ProductStore as ProductStore

from reporter.pdfgenerator import generateDepletedReport
from . import auth, api
from . import logger

@api.route('/v1.0/findProduct/<bCode>', methods=['GET'])
@auth.login_required
def findProduct(bCode):
    product = Product.query.filter_by(barcode=bCode).first()
    if (product is None):
        abort(404)
    else:
        return make_response(jsonify({'mobilerp': [product.serialize]}), 200)


@api.route('/v1.0/listProducts/', methods=['GET'])
@auth.login_required
def listProducts():
    products = ProductStore.query.order_by(ProductStore.name.asc()).all()
    if products is None:
        abort(400)
    return make_response(jsonify({'mobilerp':
                         [p.serialize for p in products]}), 200)

@api.route('/v1.0/newProduct/', methods=['POST'])
@auth.login_required
def newProduct():
    if not request.json or 'barcode' not in request.json\
       or 'units' not in request.json or 'price' not in request.json\
       or 'name' not in request.json:
        abort(400)
    if request.json['barcode'] is '' or request.json['name'] is ''\
       or request.json['units'] is '' or request.json['price'] is '':
        abort(401)
    if (logger.log_op(request.json)):
        p = Product(request.json['barcode'], request.json['name'],
                    request.json['units'], request.json['price'])
        db_session.add(p)
        db_session.commit()
        return make_response(jsonify({'mobilerp': [p.serialize]}), 200)
    else:
        return make_response(jsonify({'mobilerp': 'Operacion duplicada, saltando'}), 428)


@api.route('/v1.0/updateProduct/<bCode>', methods=['PUT'])
@auth.login_required
def updateProduct(bCode):
    if not request.json:
        abort(400)
    p = Product.query.filter_by(barcode=bCode).first()
    if p is None:
        abort(404)
    if (logger.log_op(request.json)):
        if 'price' in request.json:
            if str(p.price) != request.json['price']:
                price_update = PriceHistory(p.barcode)
                db_session.add(price_update)
                db_session.commit()
                p.price = float(request.json['price'])
        if 'units' in request.json:
            p.units = p.units + int(request.json['units'])
        if 'name' in request.json:
            p.name = request.json['name']
        db_session.add(p)
        db_session.commit()
        return make_response(jsonify({'mobilerp': [p.serialize]}), 200)
    else:
        return make_response(jsonify({'mobilerp': 'Operacion duplicada, saltando'}), 428)

@api.route('/v1.0/listDepletedProducts/', methods=['GET'])
@auth.login_required
def listDepletedProducts():
    products = DepletedItems.query.all()
    if products is None:
        abort(400)
    data = {'mobilerp': [p.serialize for p in products]}
    generateDepletedReport(data)
    return make_response(jsonify(data), 200)

################################## V1.1 #######################################

@api.route('/v1.1/listProducts/<int:storeid>', methods=['GET'])
@auth.login_required
def listProducts_v1_1(storeid):
    products = ProductStore.query.filter_by(storeid=storeid).order_by(ProductStore.name.asc()).all()
    if products is None:
        abort(400)
    return make_response(jsonify({'mobilerp':
                         [p.serialize for p in products]}), 200)

@api.route('/v1.1/findProduct/<bCode>', methods=['GET'])
@auth.login_required
def findProduct_v1_1(bCode):
    product = MasterList.query.filter_by(barcode=bCode).first()
    if (product is None):
        abort(404)
    else:
        return make_response(jsonify({'mobilerp': [product.serialize]}), 200)

@api.route('/v1.1/newProduct/', methods=['POST'])
@auth.login_required
def newProduct_v1_1():
    if not request.json or 'barcode' not in request.json\
       or 'units' not in request.json or 'price' not in request.json\
       or 'name' not in request.json or 'storeid' not in request.json :
        abort(400)
    if request.json['barcode'] is '' or request.json['name'] is ''\
       or request.json['units'] is '' or request.json['price'] is ''\
       or request.json['storeid'] is '':
        abort(401)
    if (logger.log_op(request.json)):
        m = MasterList(request.json['barcode'], request.json['name'],
            request.json['price'])
        db_session.add(m)
        db_session.commit()
        p = Product(request.json['barcode'], request.json['units'],
            request.json['storeid'])
        db_session.add(p)
        db_session.commit()
        return make_response(jsonify({'mobilerp': [p.serialize]}), 200)
    else:
        return make_response(jsonify({'mobilerp': 'Operacion duplicada, saltando'}), 428)


@api.route('/v1.1/updateProduct/<bCode>', methods=['PUT'])
@auth.login_required
def updateProduct_v1_1(bCode):
    if not request.json or 'storeid' not in request.json:
        abort(400)
    m = MasterList.query.filter_by(barcode=bCode).first()
    if m is None:
        abort(404)
    if (logger.log_op(request.json)):
        if 'price' in request.json:
            if str(m.price) != request.json['price']:
                price_update = PriceHistory(m.barcode)
                db_session.add(price_update)
                db_session.commit()
                m.price = float(request.json['price'])
        if 'name' in request.json:
            m.name = request.json['name']
        db_session.add(m)
        db_session.commit()
        p = None
        if 'units' in request.json:
            engine.execute(updateHelper(bCode, int(request.json['units']), int(request.json['storeid'])))
        else:
            engine.execute(updateHelper(bCode, 0, int(request.json['storeid'])))
        return make_response(jsonify({'mobilerp': [m.serialize]}), 200)
    else:
        return make_response(jsonify({'mobilerp': 'Operacion duplicada, saltando'}), 428)

@api.route('/v1.1/listDepletedProducts/<storeid>', methods=['GET'])
@auth.login_required
def listDepletedProducts_v1_1(storeid):
    products = DepletedItems.query.filter_by(storeid=int(storeid)).all()
    if products is None:
        abort(400)
    data = {'mobilerp': [p.serialize for p in products]}
    generateDepletedReport(data)
    return make_response(jsonify(data), 200)

def updateHelper(barcode, units, storeid):
    p = Product.query.filter_by(storeid=storeid, barcode=barcode).first()
    if p is None:
        p = Product(barcode, 0, storeid)
    db_session.add(p)
    db_session.commit()
    u = p.units - units
    return "UPDATE product set units={0} where barcode='{1}' and storeid={2}"\
        .format(u, barcode, storeid)

