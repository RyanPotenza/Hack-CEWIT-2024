from EVRoutePlanner import EVRoutePlanner

with open("./APIKey.txt") as f:
    api_key = f.readline()

def EVEmissions(client, start, fin, battery):
    return 1

def calculateOptimalEVRoute(client, start, end, battery):
    # Return a list of waypoints to be used in
    # start = (40.743462, -74.029068)
    # end = (42.886448, -78.878372)

    print("PRESSSED ")

    ev_route_planner = EVRoutePlanner(api_key, start, end, int(battery)*1000) 
    route = ev_route_planner.calculate_route()
    
    waypoints = ev_route_planner.charging_stations
    # waypoints = [{'lat': 40.743462, 'lng': -74.029068}, {'lat': 42.886448, 'lng': -78.878372}]

    return waypoints

