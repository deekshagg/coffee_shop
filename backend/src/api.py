import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
with app.app_context():
    setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
# db_drop_and_create_all(app)


@app.route("/")
def index():
    return "Hello, World!"


@app.route('/drinks', methods=['GET'])
def get_drinks():
    try:
        with app.app_context():
            drinks = Drink.query.all()

        drinks_short = [drink.short() for drink in drinks]

        response = {
            'success': True,
            'drinks': drinks_short
        }

        return jsonify(response), 200

    except Exception as e:
        print(e)

        return jsonify({'success': False, 'error': 'Failed to retrieve drinks'}), 500


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    try:
        with app.app_context():
            drinks = Drink.query.all()

        drinks_long = [drink.long() for drink in drinks]
        response = {'success': True, 'drinks': drinks_long}
        return jsonify(response), 200

    except Exception as e:
        print(e)

        return jsonify({'success': False, 'error': 'Failed to retrieve drinks'}), 500


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(payload):
    try:
        data = request.json
        new_drink = Drink(title=data['title'],
                          recipe=json.dumps(data['recipe']))

        Drink.insert(new_drink)

        return jsonify({"success": True, "drinks": [Drink.long(new_drink)]}), 200
    except Exception as e:
        print(e)
        return jsonify({"success": False, "error": "UnAuthorised User"}), 401


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, drink_id):
    try:
        drink = Drink.query.get(drink_id)

        if not drink:
            return jsonify({"success": False, "error": "Drink not found"}), 404

        data = request.json

        drink.title = data.get('title', drink.title)
        drink.recipe = json.dumps(data.get('recipe', drink.recipe))

        Drink.update(drink)

        return jsonify({"success": True, "drinks": [Drink.long(drink)]}), 200
    except Exception as e:
        print(e)
        Drink.rollback()
        return jsonify({"success": False, "error": "UnAuthorised User"}), 401


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, drink_id):
    try:
        drink = Drink.query.get(drink_id)

        if not drink:
            return jsonify({"success": False, "error": "Drink not found"}), 404

        Drink.delete(drink)

        return jsonify({"success": True, "delete": drink_id}), 200
    except Exception as e:
        print(e)

        Drink.rollback()
        return jsonify({"success": False, "error": "UnAuthorised User"}), 401


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "Resource not found"
    }), 404


@app.errorhandler(401)
def not_found_error(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "UnAuthorised"
    }), 404


@app.errorhandler(AuthError)
def handle_auth_error(e):
    response = jsonify(e.error)
    response.status_code = e.status_code
    return response
