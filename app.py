from flask import Flask, jsonify, render_template, url_for, make_response, redirect
from flask_restful import Api, Resource, reqparse, abort, request, marshal
from flask_sqlalchemy import SQLAlchemy
import datetime
import json
from flask_marshmallow import Marshmallow


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
api = Api(app)
db = SQLAlchemy(app)
parser = reqparse.RequestParser()
ma = Marshmallow(app)

class Meter(db.Model):
    serialize_only = ('id', 'label')
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    label = db.Column(db.String(255), nullable=False)
    meterdata = db.relationship('MeterData', cascade="all, delete")

class meterSchema(ma.Schema):
    class Meta:
        fields = ("id", "label", "_links")

meter_schema = meterSchema()

class MeterData(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    meter_id = db.Column(db.Integer, db.ForeignKey(Meter.id), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    value = db.Column(db.Float, nullable=False)

class meterDataSchema(ma.Schema):
    class Meta:
        fields = ('id', 'meter_id', 'timestamp', 'value')

meter_data_schema = meterDataSchema(many=True)

with app.app_context():
    db.create_all()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/meters', methods=['GET'])
def meter_list():
    meters = Meter.query.all()
    if 'HX-Request' in request.headers:
        return render_template('partials/meters_list.html', meters=meters)
    else:
        return render_template('meters_list.html', meters=meters)

@app.route('/meter/<int:id>', methods=['GET'])
def meter_detail(id):
    meter = Meter.query.get(id)
    meterData = MeterData.query.filter_by(
        meter_id=id).order_by(MeterData.timestamp.desc())
    if meter is None:
        abort(404)
    if 'HX-Request' in request.headers:
        return render_template('partials/meter_details.html', meter=meter_schema.dump(meter), meterData=meterData, meterDataJson=meter_data_schema.dump(meterData))
    else:
        return render_template('meter_details.html', meter=meter_schema.dump(meter), meterData=meterData, meterDataJson=meter_data_schema.dump(meterData))

@app.route('/meters/create', methods=['POST', 'GET'])
def meter_create():
    if request.method == 'POST':
        parser.add_argument('label', type=str, required=True)
        meter = Meter(
            label=request.form['label']
        )
        db.session.add(meter)
        db.session.commit()
        toast = {
            "message": f'Meter {meter.label} was successfuly CREATED @ {datetime.datetime.now(datetime.timezone.utc)} with an ID of {meter.id}'
        }
        resp = make_response(render_template('partials/meter_details.html', meter=meter_schema.dump(
            meter), meterData=json.dumps({}), meterDataJson=json.dumps({})), 201)
        resp.headers['HX-Trigger'] = json.dumps(
            {'showToast': f'{toast["message"]}'})
        resp.headers['HX-Target'] = "#pushedContent"
        resp.headers['HX-Push'] = f'/meter/{meter.id}'
        return resp

@app.route('/meter/<int:id>/delete', methods=['GET', 'DELETE'])
def meter_delete(id):
    meter = Meter.query.get(id)
    if meter is None:
        abort(404)
    if request.method == 'DELETE':
        db.session.delete(meter)
        db.session.commit()
        toast = {
            "message": f'Meter {meter.label} was successfuly DELETED @ {datetime.datetime.now(datetime.timezone.utc)} with an ID of {meter.id}'
        }
        resp = make_response(render_template(
            'partials/meters_list.html', meters=Meter.query.all()), 302)
        resp.headers['HX-Trigger'] = json.dumps(
            {'showToast': f'{toast["message"]}'})
        resp.headers['HX-Target'] = "#pushedContent"
        resp.headers['HX-Push'] = '/meters'
        return resp

@app.route('/meter/<int:id>/update', methods=['GET', 'PUT'])
def meter_update(id):
    parser.add_argument('id', type=int, required=True)
    parser.add_argument('label', type=str, required=True)
    meter = Meter.query.get(id)
    if meter is None:
        abort(404)
    if request.method == 'PUT':
        meter.label = request.form['label']
        db.session.commit()
        toast = {
            "message": f'Meter {meter.label} was successfuly UPDATED @ {datetime.datetime.now(datetime.timezone.utc)} with an ID of {meter.id}'
        }
        resp = make_response(render_template(
            'partials/meter_details.html', meter=meter_schema.dump(meter)), 201)
        resp.headers['HX-Trigger'] = json.dumps(
            {'showToast': f'{toast["message"]}'})
        resp.headers['HX-Target'] = "#pushedContent"
        resp.headers['HX-Push'] = f'/meter/{meter.id}'
        return resp

@app.route('/meter/<int:id>/data/create', methods=['GET', 'POST'])
def create_meter_data(id):
    if request.method == 'POST':
        parser.add_argument('id', type=int, required=True)
        parser.add_argument('value', type=int, required=True)
        meter = Meter.query.get(id)
        meterData = MeterData(
            meter_id=id,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            value=request.form['value']
        )
        db.session.add(meterData)
        db.session.commit()
        meterDataList = MeterData.query.filter_by(
            meter_id=id).order_by(MeterData.timestamp.desc())
        toast = {
            "message": f'Meter Data for {meter.label} was successfuly CREATED @ {datetime.datetime.now(datetime.timezone.utc)} with an ID of {meterData.id} with a value of {meterData.value}',
        }
        resp = make_response(render_template('partials/meter_data.html', meter=meter,
                             meterData=meterDataList, meterDataJson=meter_data_schema.dump(meterDataList)), 201)
        resp.headers['HX-Trigger'] = json.dumps(
            {'showToast': f'{toast["message"]}'})
        resp.headers['HX-Target'] = "#meter_data_partial"
        resp.headers['HX-Push'] = f'/meter/{id}'
        return resp

if __name__ == '__main__':
   app.run()
