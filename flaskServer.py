from flask import Flask, request
from flask_restful import Resource, Api
from EVNav import *
from AltNav import *

app = Flask(__name__)
api = Api(app)

class EVRoute(Resource):
    def post(self):
        # Parse the JSON input
        data = request.get_json()

        # Extract fields from the input JSON
        ev_battery_capacity = data.get('ev_battery_capacity')
        starting_location = data.get('starting_location')
        destination_location = data.get('destination_location')

        # For demonstration, echo the received data back in the response
        response_data = {
            'ev_battery_capacity': ev_battery_capacity,
            'starting_location': starting_location,
            'destination_location': destination_location
        }

        # In a real application, you would add logic here to process the data,
        # such as calculating the optimal route, and then return that information.

        return {'status': 'success', 'data': response_data}, 200

# Add the EVRoute resource to the API
api.add_resource(EVRoute, '/evroute')

if __name__ == '__main__':
    app.run(debug=True)
