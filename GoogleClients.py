import googlemaps
import polyline
from geopy.distance import geodesic
from typing import List, Tuple
from math import sin, cos, sqrt, atan2, radians

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

