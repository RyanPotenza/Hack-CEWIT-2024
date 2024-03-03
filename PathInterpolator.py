import googlemaps
import polyline
from geopy.distance import geodesic

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
