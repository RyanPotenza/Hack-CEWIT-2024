from flask import Flask, request, render_template, jsonify, send_file
from flask_restful import Resource, Api
from flask_cors import CORS
import json

from EVNav import *
from utils import *

app = Flask(__name__, static_url_path='/static', static_folder='static')
api = Api(app)

client = get_client()

CORS(app) #Enable Cross-Origin Resource Sharing

@app.route('/get-ev-models')
def get_ev_models():
    ev_models = r.hgetall('ev_models')  # Assuming data is stored in a hash
    ev_models_dict = {key.decode('utf-8'): value.decode('utf-8') for key, value in ev_models.items()}
    return jsonify(ev_models_dict)

class EVRoute(Resource):
    def post(self):
        # Parse the JSON input
        data = request.get_json()

        # Extract fields from the input JSON
        ev_battery_capacity     = data.get('ev_battery_capacity')
        ev_total_range          = data.get('ev_total_range')
        starting_location       = data.get('starting_location')
        destination_location    = data.get('destination_location')

        #calculate EV optimal route
        ev_waypoints = calculateOptimalEVRoute(client, starting_location, destination_location, ev_battery_capacity)
        print(f"Waypoints: {ev_waypoints}")
        
        # Calculate emissions
        ev_emissions = EVEmissions(client, starting_location, destination_location, ev_battery_capacity)
        
        # Prepare response data
        response_data = {
            'emissions':        ev_emissions,
            'ev_waypoints':     ev_waypoints,
            'start_location':   starting_location,
            'end_location':     destination_location,
        }

        return {'status': 'success', 'data': response_data}, 200

# Add the EVRoute resource to the API
api.add_resource(EVRoute, '/evroute')

@app.route('/')
def index():
    # Get the API key from the file
    api_key = getAPIKey('APIKey.txt')
    
    # Render the HTML template and pass the API key
    return render_template('index.html', api_key=api_key)

@app.route('/map.html')
def map():
    api_key = getAPIKey('APIKey.txt')

    return render_template('map.html', api_key=api_key)

@app.route('/evdata')
def serve_data():
    with open('data/evdata.json', 'r') as file:
        evdata = json.load(file)
    return jsonify(evdata)

if __name__ == '__main__':
    app.run(debug=True)
    

