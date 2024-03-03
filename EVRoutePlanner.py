import googlemaps
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go

import polyline

from typing import List, Dict, Any, Tuple
from math import sin, cos, sqrt, atan2, radians 
from geopy.distance import geodesic

power_plants = pd.read_csv("global_power_plant_database.csv", header=0)
co2_emissions = {
    'Hydro': 4,
    'Solar': 45,
    'Gas': 450,
    'Other': 0,  # This is a placeholder, as "Other" is not specific
    'Oil': 890,
    'Wind': 11,
    'Nuclear': 12,
    'Coal': 1001,
    'Waste': 670,  # This is an estimate; actual emissions can vary
    'Biomass': 230,
    'Wave and Tidal': 17,  # This is an estimate; actual emissions can vary
    'Petcoke': 1025,  # This is an estimate; actual emissions can vary
    'Geothermal': 38,
    'Storage': 0,  # This depends on the source of the stored energy
    'Cogeneration': 0  # This is a placeholder, as emissions depend on the fuel used
} # kg CO2 per MWh

class EmissionsCalculator:
    def __init__(self, vehicle_type='Model 3'):
        self.vehicle_type = vehicle_type
        # Define the energy consumption in Wh/km for different vehicle types
        self.energy_consumption = {
            'Model 3': 139,  # Tesla Model 3: 139 Wh/km
            # Add other vehicle types here if needed
        }

    def haversine(self, lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = 6371000 * c  # Radius of earth in meters
        return distance

    def is_within_distance(self, lat1, lon1, lat2, lon2, dist):
        """
        Check if a point at lat2, lon2 is within dist meters from lat1, lon1
        """
        distance = self.haversine(lat1, lon1, lat2, lon2)
        return distance <= dist

    def get_power_plant_emission(self, lat, lon, power_plants, co2_emissions):
        """
        Returns kgCO2 / m based on the location and nearby power plants
        """
        # Get power plants in a 20km radius
        power_plants_near = power_plants[power_plants.apply(lambda row: self.is_within_distance(lat, lon, row['latitude'], row['longitude'], 20000), axis=1)]

        # Get the fraction of each type of power plant based on primary_fuel and capacity_mw
        power_plant_type_fraction = power_plants_near.groupby('primary_fuel').sum()['capacity_mw'] / power_plants_near['capacity_mw'].sum()
        power_plant_type_emissions = (power_plant_type_fraction * pd.Series(co2_emissions)).sum()  # kg CO2 per MWh

        # Convert energy consumption to Wh/m and calculate emissions
        energy_consumption_wh_per_m = self.energy_consumption[self.vehicle_type] / 1000
        return power_plant_type_emissions * energy_consumption_wh_per_m * 1e-6  # kg CO2 / m
    
    def calculate_emissions(self, total_charge, loc):
        """
        Calculate the CO2 emissions for a given location
        """
        return self.get_power_plant_emission(loc['lat'], loc['lng'], power_plants, co2_emissions) * total_charge


class PathInterpolator:
    def __init__(self, api_key, interval_meters=10000):
        self.gmaps = googlemaps.Client(key=api_key)
        self.interval_meters = interval_meters

    def get_points_at_intervals(self, origin, destination):
        # # Request directions
        directions_result = self.gmaps.directions(origin, destination)

        # Extract the encoded polyline
        # encoded_polyline = route['overview_polyline']['points']
        encoded_polyline = directions_result[0]['overview_polyline']['points']

        # Decode the polyline to get a list of latitude and longitude points
        path = polyline.decode(encoded_polyline)

        print("HERE")

        
        # print(path)

        # Interpolate points along the path
        return self._interpolate_points(path, self.interval_meters)

    def _interpolate_points(self, path, interval_meters):
        points = [path[0]]
        remaining_distance = interval_meters
        for i in range(1, len(path)):
            # Calculate the distance between the current and next point
            distance = geodesic(path[i - 1], path[i]).meters
            while distance >= remaining_distance:
                # Interpolate a new point along the segment
                ratio = remaining_distance / distance
                new_point = (
                    path[i - 1][0] + ratio * (path[i][0] - path[i - 1][0]),
                    path[i - 1][1] + ratio * (path[i][1] - path[i - 1][1])
                )
                points.append(new_point)
                path[i - 1] = new_point
                distance -= remaining_distance
                remaining_distance = interval_meters
            remaining_distance -= distance
        return points

# origin = 'New York, NY'
# destination = 'Los Angeles, CA'
# interval_meters = 10000  # 10 kilometers

# interpolator = PathInterpolator(api_key)
# points = interpolator.get_points_at_intervals(origin, destination, interval_meters)
# print(points)

class GooglePlacesClient:
    def __init__(self, api_key: str):
        """
        Initializes the GooglePlacesClient with a given API key.

        :param api_key: Google Places API key.
        """
        self.client = googlemaps.Client(key=api_key)

    def find_nearby_charging_stations(self, location: Tuple[float, float],  radius: int = 10000) -> List[dict]:
        """
        Finds nearby EV charging stations within a specified radius from the current location.

        :param location: A tuple containing the latitude and longitude of the current location.
        :param radius: Search radius in meters. Default is 10,000 meters (10 km).
        :return: A list of dictionaries containing information about each charging station found.
        """
        results = self.client.places_nearby(
            location=location,
            radius=radius,
            type="electric_vehicle_charging_station"
        )

        if not results or 'results' not in results or len(results['results']) == 0:
            return []

        return results['results']
class GoogleMapsClient:
    def __init__(self, api_key: str):
        self.client = googlemaps.Client(key=api_key)

    def get_route(self, start: Tuple[float, float], end: Tuple[float, float]) -> dict:
        """
        Fetches route information from start to end using Google Maps API.

        :param start: A tuple containing the latitude and longitude of the start point.
        :param end: A tuple containing the latitude and longitude of the end point.
        :return: Route information as a dictionary.
        """
        routes = self.client.directions(start, end, mode="driving", units="metric")
        if not routes:
            raise ValueError("No routes found")
        return routes[0]

class EVRoutePlanner:
    def __init__(self, api_key: str, start: Tuple[float, float], end: Tuple[float, float], vehicle_range: int):
        """
        Initializes the EVRoutePlanner with start, end locations, and the EV's range.

        :param api_key: API key for accessing Google Maps and Places APIs.
        :param start: Start location as a tuple (latitude, longitude).
        :param end: End location as a tuple (latitude, longitude).
        :param vehicle_range: The EV's range on a full charge in meters.
        """
        self.maps_client = GoogleMapsClient(api_key)
        self.places_client = GooglePlacesClient(api_key)
        self.paths_interpolator = PathInterpolator(api_key,30000)
        self.emissions_calculator = EmissionsCalculator()
        self.start = start
        self.end = end
        self.vehicle_range = vehicle_range
        self.route = []
        self.total_distance = 0

        self.emissions_kg_co2 = 0

        self.charging_stations = []

        self.all_stations = []

    def calculate_route(self) -> List[dict]:
        """
        Calculates the route, including necessary charging stops based on the EV's range.

        :return: A list of route segments, including charging stops.
        """
        current_location = self.start
        keepGoing = True
        while keepGoing:
            # try:
            # route_segment = self.maps_client.get_route(current_location, self.end)
            path = self.paths_interpolator.get_points_at_intervals(current_location, self.end)

            nodes = self.path_to_nodes(path)

            # self.end = (nodes[-1]['lat'], nodes[-1]['lng'])
            for i, node in enumerate(nodes):
                print(f"Processing node {i + 1} of {len(nodes)}")
                if self._requires_charge(node, nodes, i):
                    print("needs charge")
                    charging_station_route = node['nearest_ev_route_segment']

                    # We must add the route nodes to the route list
                    for step in charging_station_route['steps']:
                        self.route.append({
                            'lat': step['start_location']['lat'],
                            'lng': step['start_location']['lng'],
                            'dist': step['distance']['value']
                        })
                        # self.total_distance += step['distance']['value']

                    # Calculate the amount of CO2 emissions 
                    self.emissions_kg_co2 += self.emissions_calculator.calculate_emissions(self.total_distance, node)   
                    print("Total Distance: ", self.total_distance)
                    print("Added emissions: ", self.emissions_kg_co2)

                    # Reset the distance 
                    self.total_distance = 0

                    # Add the charging station to the charging stations list
                    self.charging_stations.append({
                        'lat': charging_station_route['end_location']['lat'],
                        'lng': charging_station_route['end_location']['lng']
                    })

                    # Recalculate route from charging station to end
                    current_location = (charging_station_route['steps'][-1]['end_location']['lat'], charging_station_route['steps'][-1]['end_location']['lng'])
                    break
                else:
                    self.route.append(node)
                    self.total_distance += node['dist']
                    if i == len(nodes) - 1:
                        # current_location = self.end
                        keepGoing = False
            # except Exception as e:
            #     print(f"Error calculating route: {e}")
            #     break
        return self.route
    
    def _requires_charge(self, current_node, nodes, current_node_i) -> bool:
        """
        Determines if charging is required based on the EV's current range,
        the distance to the next node, and the distance from the next node to the nearest charging station.

        :param current_node: The current node in the route.
        :param nodes: List of all nodes
        :param current_node_i: The index of the current node in the list of nodes
        :return: True if charging is required before reaching the next node, False otherwise.
        """

        if not nodes:
            return False
        if 'nearest_ev_station_distance' in current_node:
            currentDist = self.total_distance
            while current_node_i < len(nodes):
                currentDist += nodes[current_node_i]['dist']
                if 'nearest_ev_station_distance' in nodes[current_node_i]:
                    currentDist += nodes[current_node_i]['nearest_ev_station_distance']
                    # print(f"Nearest station distance: {nodes[current_node_i]['nearest_ev_station_distance']}")
                    print(f"Current distance: {currentDist}")
                    return currentDist > self.vehicle_range
                current_node_i += 1
            return False

    def path_to_nodes(self, path) -> List[dict]:
        """
        Converts a route segment to a list of nodes, where each node represents a step in the route
        with its start location (latitude and longitude) and distance.

        :param route_segment: Segment of the route as returned by the Google Maps API.
        :return: A list of nodes, each containing latitude, longitude, and distance.
        """
        nodes = []
        # Iterate through each step in the route segment
        for step in path:
            dist = 0
            if not (step == path[-1]):
                # Calculate the distance between the current and next step
                dist = geodesic(step, path[path.index(step) + 1]).meters
                # print(dist)

            node = {
                'lat': step[0],
                'lng': step[1],
                'dist': dist
            }
            # Calculate the distance to the nearest EV charging station
            nearest_station = self.places_client.find_nearby_charging_stations((node['lat'], node['lng']))[0]#['geometry']['location']

            if nearest_station:
                nearest_station_route = self.maps_client.get_route((node['lat'], node['lng']), (nearest_station['geometry']['location']['lat'], nearest_station['geometry']['location']['lng']))['legs'][0]
                nearest_station_distance = nearest_station_route['distance']['value']

                node['nearest_ev_station'] = nearest_station
                node['nearest_ev_station_distance'] = nearest_station_distance
                node['nearest_ev_route_segment'] = nearest_station_route


            nodes.append(node)
        return nodes
    
    
