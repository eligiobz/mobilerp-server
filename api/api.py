#!env/bin/python

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

from flask import Blueprint, abort, url_for,  Flask, jsonify, abort, make_response, request
from flask_httpauth import HTTPBasicAuth

from models import Base, engine, db_session
from models.User import User
from models.Product import Product
from models.Sale import Sale
from models.SaleDetails import SaleDetails
from models.PriceHistory import PriceHistory
from models import db_session as db_session, engine as engine

from flask_compress import Compress
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

api = Blueprint('api', __name__, 'templates')
auth = HTTPBasicAuth()

@api.route('/v1.0/findProduct/<int:bCode>', methods=['GET'])
@auth.login_required
def findProduct(bCode):
    product = Product.query.filter_by(barcode=bCode).first()
    if (product == None):
        abort(404)
    else:
        return make_response(jsonify({'mobilerp' : [product.serialize]}), 200)

@api.route('/v1.0/listProducts/', methods=['GET'])
@auth.login_required
def listProducts():
    products = Product.query.all()
    if products is None:
        abort(400)
    return make_response(jsonify({'mobilerp' : [p.serialize for p in products]}), 200)

@api.route('/v1.0/newProduct/', methods=['POST'])
@auth.login_required
def newProduct():
    if not request.json or not 'barcode' in request.json or not 'units' in request.json or not 'price' in request.json or not 'name' in request.json:
        abort(400)
    p = Product(request.json['barcode'], request.json['name'], 
        request.json['units'], request.json['price'])
    db_session.add(p)
    db_session.commit()
    return make_response(jsonify({'mobilerp' : [p.serialize]}), 200)

@api.route('/v1.0/updateProduct/<int:bCode>', methods=['PUT'])
@auth.login_required
def updateProduct(bCode):
    if not request.json:
        abort(400)
    p = Product.query.filter_by(barcode=bCode).first()
    if p is None:
        abort(404)
    if 'price' in request.json:
        if str(p.price) != request.json['price']:
            price_update = PriceHistory(p.barcode)
            db_session.add(price_update)
            db_session.commit()
            p.price = float(request.json['price'])
    if 'units' in request.json :
        p.units = p.units + int(request.json['units'])
    db_session.add(p)
    db_session.commit()
    print ("Update Done")
    return make_response(jsonify({'mobilerp' : [p.serialize]}), 200)

@api.route('/v1.0/makeSale', methods=['POST'])
@auth.login_required
def makeSale():
    if not request.json:
        abort(400)
    if 'barcode' not in request.json or len(request.json['barcode']) <= 0:
        abort(400)
    s = Sale()
    db_session.add(s)
    db_session.commit()
    for i in range(0, len(request.json['barcode'])):
        bCode = request.json['barcode'][i]
        units = request.json['units'][i]
        print(bCode, units)
        ps = Product.query.filter_by(barcode=bCode).first()
        if (ps.units - units < 0):
            abort(406)
        else:
            sd = SaleDetails(s.id, ps.barcode, ps.price, units)
            ps.units = ps.units - units
            db_session.add(ps)
            db_session.add(sd)
            db_session.commit()
    return make_response(jsonify({'mobilerp' : '[p.serialize]'}), 200)

@api.route('/v1.0/listDepletedProducts/', methods=['GET'])
@auth.login_required
def listDepletedProducts():
    products = Product.query.filter_by(units=0).all()
    if products is None:
        abort(400)
    return make_response(jsonify({'mobilerp' : [p.serialize for p in products]}), 200)

@api.route('/v1.0/dailyReport', methods=['GET'])
@auth.login_required
def sendDailyReport():
    cdate = ddate.today()
    return make_response(jsonify({'mobilerp': salesReport(cdate)}), 200)


@api.route('/v1.0/monthlyReport', methods=['GET'])
@auth.login_required
def sendMonthlyReport():
    cdate = ddate.today()
    return make_response(jsonify({'mobilerp': salesReport(cdate, 30)}), 200)

@api.route('/blueprint')
def show():
    return url_for('/static/pdf/2017-08-02.pdf')

##################################### AUTH #####################################

@auth.get_password
def get_password(user):
    user = User.query.filter_by(username=user).first()
    if user == None:
        return None
    return user.password

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)

################################## USERS API ##################################

## New User
@api.route('/v1.0/users', methods=['POST'])
def add_user():
    if not request.json or (not 'user' in request.json and not 'pass' in request.json 
        or not 'level' in request.json):
        abort(403)
    user = User(request.json['user'], request.json['pass'], request.json['level'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'mobilerp':user.getUser()})

## Update User
@api.route('/v1.0/users/<string:n_pass>', methods=['PUT'])
@auth.login_required
def update_pass(n_pass):
    user = User.query.filter_by(email=auth.username()).first()
    user.password = n_pass
    db.session.add(user)
    db.session.commit()
    return jsonify({'user':user.getUser()})

@api.route('/v1.0/user/checkLogin/', methods=['GET'])
@auth.login_required
def checkLogin():
    return make_response(jsonify({'logged': 'true'}), 200)
