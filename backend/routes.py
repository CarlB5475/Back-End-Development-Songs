from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)


def parse_json(data):
    return json.loads(json_util.dumps(data))


######################################################################
# INSERT CODE HERE
######################################################################
@app.get('/health')
def health():
    return {"status": "OK"}, 200


@app.get('/count')
def count():
    return {"count": db.songs.count_documents({})}, 200


@app.get('/song')
def songs():
    songs_list = list(db.songs.find({}))
    return {"songs": parse_json(songs_list)}, 200


@app.get('/song/<int:id>')
def get_song_by_id(id):
    song = db.songs.find_one({"id": id})
    if not song:
        return {"message": "song with id not found"}, 404

    return parse_json(song), 200


@app.post('/song')
def create_song():
    song_data = request.get_json()

    existing_song = db.songs.find_one({"id": song_data["id"]})
    if existing_song:
        return {
            "Message": f"song with id {existing_song['id']} already presentd"
            }, 302

    inserted_id = db.songs.insert_one(song_data).inserted_id
    return {"inserted id": parse_json(inserted_id)}, 201


@app.put('/song/<int:id>')
def update_song(id):
    song_data = request.get_json()

    existing_song = db.songs.find_one({"id": id})
    if not existing_song:
        return {"message": "song not found"}, 404

    comparison_values = {"id": id}
    comparison_values.update(song_data)
    same_song = db.songs.find_one(comparison_values)
    if same_song:
        return {"message": "song found, but nothing updated"}, 200

    db.songs.update_one({"id": id}, {"$set": song_data})
    updated_song = db.songs.find_one({"id": id})
    return parse_json(updated_song), 201


@app.delete('/song/<int:id>')
def delete_song(id):
    res = db.songs.delete_one({"id": id})
    if res.deleted_count == 0:
        return {"message": "song not found"}, 404

    return "", 204
