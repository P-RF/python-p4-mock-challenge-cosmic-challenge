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

    def delete(self, id):
        scientist = Scientist.query.filter(Scientist.id == id).first()

        if not scientist:
            return {"error": "Scientist not found"}, 404
        
        db.session.delete(scientist)
        db.session.commit()

        return '', 204

api.add_resource(Scientists, '/scientists')
api.add_resource(ScientistByID, '/scientists/<int:id>')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
