#!/usr/bin/env python3

from models import db, Scientist, Mission, Planet
from flask_restful import Api, Resource
from flask_migrate import Migrate
from flask import Flask, make_response, jsonify, request
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get(
    "DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

db.init_app(app)

migrate = Migrate(app, db)

api = Api(app)


@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Cosmic API"}), 200

class Scientists(Resource):
    def get(self):
        scientists = [s.to_dict(only=('id', 'name', 'field_of_study')) for s in Scientist.query.all()]
        return scientists, 200

    def post(self):
        request_data = request.get_json()

        errors = []
        for field in ['name', 'field_of_study']:
            if field not in request_data or not request_data[field]:
                return {"errors": ["validation errors"]}, 400

        scientist = Scientist(
            name=request_data['name'],
            field_of_study=request_data['field_of_study']
        )

        db.session.add(scientist)
        db.session.commit()

        response = scientist.to_dict(only=('id', 'name', 'field_of_study'))
        response['missions'] = []

        return response, 201

class ScientistByID(Resource):
    def get(self, id):
        scientist = Scientist.query.filter_by(id=id).first()
        if not scientist:
            return {"error": "Scientist not found"}, 404

        response_dict = {
            "field_of_study": scientist.field_of_study,
            "id": scientist.id,
            "name": scientist.name,
            'missions': []
        }

        for mission in scientist.missions:
            mission_dict = {
                "id": mission.id,
                "name": mission.name,
                "planet": {
                    "distance_from_earth": mission.planet.distance_from_earth,
                    "id": mission.planet.id,
                    "name": mission.planet.name,
                    "nearest_star": mission.planet.nearest_star
                },
                "planet_id": mission.planet_id,
                "scientist_id": mission.scientist_id
            }
            response_dict["missions"].append(mission_dict)

        return response_dict, 200

    def patch(self, id):
        scientist = Scientist.query.filter_by(id=id).first()
        if not scientist:
            return {"error": "Scientist not found"}, 404

        request_data = request.get_json()

        # Validate fields
        if 'name' in request_data and not request_data['name']:
            return {"errors": ["validation errors"]}, 400
        if 'field_of_study' in request_data and not request_data['field_of_study']:
            return {"errors": ["validation errors"]}, 400

        # Update fields
        if 'name' in request_data:
            scientist.name = request_data['name']
        if 'field_of_study' in request_data:
            scientist.field_of_study = request_data['field_of_study']

        db.session.commit()

        response_dict = scientist.to_dict(only=('id', 'name', 'field_of_study'))
        response_dict['missions'] = [m.to_dict(
            only=('id', 'name', 'planet_id', 'scientist_id'),
            include=('planet',)
        ) for m in scientist.missions]

        return response_dict, 202

    def delete(self, id):
        scientist = Scientist.query.filter(Scientist.id == id).first()

        if not scientist:
            return {"error": "Scientist not found"}, 404
        
        db.session.delete(scientist)
        db.session.commit()

        return '', 204

class Planets(Resource):
    def get(self):
        planets = [p.to_dict(only=("id", "name", "distance_from_earth", "nearest_star")) for p in Planet.query.all()]
        return planets, 200


class Missions(Resource):
    def post(self):
        request_data = request.get_json()

        errors = []
        for field in ['name', 'scientist_id', 'planet_id']:
            if field not in request_data or not request_data[field]:
                return {"errors": ["validation errors"]}, 400

        mission = Mission (
            name=request_data['name'],
            scientist_id=request_data['scientist_id'],
            planet_id=request_data['planet_id']
        )
        
        db.session.add(mission)
        db.session.commit()

        response = mission.to_dict(only=("id", "name", "planet_id", "scientist_id"))
        
        response['scientist'] = mission.scientist.to_dict(only=('id', 'name', 'field_of_study'))
        response['planet'] = mission.planet.to_dict(only=('id', 'name', 'distance_from_earth', 'nearest_star'))

        return response, 201

api.add_resource(Scientists, '/scientists')
api.add_resource(ScientistByID, '/scientists/<int:id>')
api.add_resource(Planets, '/planets')
api.add_resource(Missions, '/missions')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
