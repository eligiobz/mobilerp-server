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

from flask import make_response, jsonify, current_app, abort
from reporter.salesreport import salesReport as salesReport
from reporter.pdfgenerator import generateSalesPdf
from . import api, auth

from datetime import datetime as ddate, timedelta
# from dateutil.parser import parser as parser


@api.route('/v1.0/daily_report/', methods=['GET'])
@api.route('/v1.1/daily_report/', methods=['GET'])
@auth.login_required
def send_daily_report():
    cdate = ddate.today()
    cdate = ddate.strptime(str(cdate.date()) +
                           " 23:59:59", "%Y-%m-%d %H:%M:%S")
    data = salesReport(cdate)
    if (data == 500):
        abort(500)
    generateSalesPdf(data)
    del(data['sales'])
    return make_response(jsonify({'mobilerp': data}), 200)


@api.route('/v1.0/monthly_report/', methods=['GET'])
@api.route('/v1.1/monthly_report/', methods=['GET'])
@auth.login_required
def send_monthly_report():
    cdate = ddate.today()
    cdate = ddate.strptime(str(cdate.date()) +
                           " 23:59:59", "%Y-%m-%d %H:%M:%S")
    data = salesReport(cdate, 30)
    if (data == 500):
        abort(500)
    generateSalesPdf(data)
    del(data['sales'])
    return make_response(jsonify({'mobilerp': data}), 200)


@api.route('/v1.1/custom_report/<init_date>/<end_date>', methods=['GET'])
@auth.login_required
def send_custom_report(init_date, end_date):
    d_init_date = ddate.strptime(init_date + " 00:00:00", "%Y-%m-%d %H:%M:%S")
    d_end_date = ddate.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
    days = (d_end_date - d_init_date).days
    if (days < 0):
        abort(400)
    if (d_end_date.date() > ddate.today().date()):
        abort(400)
    data = salesReport(d_end_date, days)
    if (data == 500):
        abort(500)
    generateSalesPdf(data)
    del(data['sales'])
    return make_response(jsonify({'mobilerp': data}), 200)


@api.route('/v1.0/get_report/<fn>', methods=['GET'])
@api.route('/v1.1/get_report/<fn>', methods=['GET'])
@auth.login_required
def get_report(fn):
    return current_app.send_static_file("pdf/" + fn)
