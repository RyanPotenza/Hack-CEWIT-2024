from EVRoutePlanner import EVRoutePlanner

with open("./APIKey.txt") as f:
    api_key = f.readline()


def calculateOptimalEVRoute(client, start, end, battery, totalRange, method):

    if method == 'default':
        range_km = int(totalRange) * 1.60934
        efficiency = int(battery)*1000/range_km
        ev_route_planner = EVRoutePlanner(api_key, start, end, range_km, efficiency) 
        route = ev_route_planner.calculate_route()
        waypoints = ev_route_planner.charging_stations
    else:
        return [], 0.0
    

    return waypoints, round(ev_route_planner.emissions_kg_co2, 3)

