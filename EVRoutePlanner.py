from typing import List, Dict, Any, Tuple
from geopy.distance import geodesic

from GoogleClients import GoogleMapsClient, GooglePlacesClient
from PathInterpolator import PathInterpolator
from EmissionsCalculator import EmissionsCalculator

class EVRoutePlanner:
    def __init__(self, api_key: str, start: Tuple[float, float], end: Tuple[float, float], vehicle_range, vehicle_efficiency):
        """
        Initializes the EVRoutePlanner with start, end locations, and the EV's range.

        :param api_key: API key for accessing Google Maps and Places APIs.
        :param start: Start location as a tuple (latitude, longitude).
        :param end: End location as a tuple (latitude, longitude).
        :param vehicle_range: The EV's range on a full charge in meters.
        """
        self.vehicle_efficiency = vehicle_efficiency
        self.vehicle_range = vehicle_range*1E3

        self.maps_client = GoogleMapsClient(api_key)
        self.places_client = GooglePlacesClient(api_key)
        self.paths_interpolator = PathInterpolator(api_key,30000)
        self.emissions_calculator = EmissionsCalculator(vehicle_efficiency)
        self.start = start
        self.end = end
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
                        # Add emissions for the last segment
                        self.emissions_kg_co2 += self.emissions_calculator.calculate_emissions(self.total_distance, node)
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
    
    
